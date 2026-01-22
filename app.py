from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import PIL.Image
import json
import os
import io
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)

# Configure Gemini API Key
API_KEY = "AIzaSyAU31UpPEw6MNOwNLZZuyfMdimertp5A40"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Load Semantic Search Resources
print("Loading Sentence Transformer model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

print("Loading FAISS index...")
try:
    search_index = faiss.read_index("furniture_vectors.index")
except Exception as e:
    print(f"Warning: Could not load FAISS index: {e}")
    search_index = None

def load_furniture_data(db_path="furniture_db.json"):
    if not os.path.exists(db_path):
        return []
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_matching_products(keyword, furniture_data):
    matches = []
    search_terms = keyword.lower().split()
    
    category_map = {
        "art": "Wall Art",
        "artwork": "Wall Art",
        "painting": "Wall Art",
        "print": "Wall Art",
        "picture": "Wall Art",
        "rug": "Rugs",
        "carpet": "Rugs",
        "lamp": "Lamps",
        "light": "Lamps",
        "lighting": "Lamps",
        "chair": "Chairs",
        "seating": "Chairs",
        "pillow": "Pillows",
        "cushion": "Pillows"
    }

    target_category = None
    for term in search_terms:
        clean_term = term.strip(".,")
        if clean_term in category_map:
            target_category = category_map[clean_term]
            break

    for item in furniture_data:
        if target_category and item['category'] == target_category:
            matches.append(item)
            continue

        item_text = (item['name'] + " " + item['description']).lower()
        if keyword in item_text:
            matches.append(item)
            continue
            
        for term in search_terms:
            clean_term = term.strip(".,")
            if len(clean_term) > 3 and clean_term in item['name'].lower():
                matches.append(item)
                break
    
    # Deduplicate matches
    unique_matches = []
    seen_ids = set()
    for m in matches:
        if m['id'] not in seen_ids:
            unique_matches.append(m)
            seen_ids.add(m['id'])
            
    return unique_matches

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Load image from memory
        image_bytes = file.read()
        img = PIL.Image.open(io.BytesIO(image_bytes))

        system_prompt = (
            "You are a Wayfair interior design expert. Analyze the room style and missing elements in this image. "
            "Then suggest specific furniture items to improve the room. "
            "Output STRICT JSON format correctly. Do NOT use markdown code blocks. "
            "Format: {\"reasoning\": \"Short reason for recommendation\", \"search_keywords\": [\"keyword1\", \"keyword2\"]}"
        )

        response = model.generate_content([system_prompt, img])
        
        text_response = response.text.strip()
        if text_response.startswith('```json'):
            text_response = text_response[7:]
        if text_response.endswith('```'):
            text_response = text_response[:-3]
        text_response = text_response.strip()

        try:
            ai_output = json.loads(text_response)
            if isinstance(ai_output, list):
                if len(ai_output) > 0:
                    ai_output = ai_output[0]
                else:
                    return jsonify({"error": "AI returned an empty list"}), 500
        except json.JSONDecodeError:
            return jsonify({
                "error": "AI response was not valid JSON",
                "raw_response": text_response
            }), 500

        reasoning = ai_output.get("reasoning", "No reasoning provided.")
        search_keywords = ai_output.get("search_keywords", [])

        furniture_data = load_furniture_data()
        
        # --- Semantic Search Logic ---
        all_recommendations = []
        seen_ids = set()
        
        # Top-K results per keyword
        k = 3 
        
        for keyword in search_keywords:
            # Vector search
            query_vector = embedder.encode([keyword]).astype('float32')
            D, I = search_index.search(query_vector, k)
            
            # I[0] contains the indices of the neighbors
            for idx in I[0]:
                if idx < len(furniture_data): # Safety check
                    product = furniture_data[idx]
                    if product['id'] not in seen_ids:
                        all_recommendations.append(product)
                        seen_ids.add(product['id'])

        return jsonify({
            "analysis": reasoning,
            "search_keywords": search_keywords,
            "recommendations": all_recommendations
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
