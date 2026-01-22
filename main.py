import google.generativeai as genai
import PIL.Image
import json
import os

# Configure Gemini API Key (Please enter your API Key here)
API_KEY = "AIzaSyDdm1ljRHMWoa0FIwqsv3S7tevpCGBrDec"

def configure_genai():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set your Google Gemini API Key in main.py.")
        return False
    genai.configure(api_key=API_KEY)
    return True

def load_furniture_data(db_path="furniture_db.json"):
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        return []
    
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_and_recommend(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image file {image_path} not found.")
        return None

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        img = PIL.Image.open(image_path)

        system_prompt = (
            "You are a Wayfair interior design expert. Analyze the room style and missing elements in this image."
            "Then suggest a specific furniture item to improve the room."
            "Finally, output ONLY the English keyword for that item (e.g., geometric rug), do not output other text."
        )

        response = model.generate_content([system_prompt, img])
        
        # Clean response text
        keyword = response.text.strip().lower()
        # Remove trailing period if present
        if keyword.endswith('.'):
            keyword = keyword[:-1]
            
        return keyword

    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return None

def find_matching_products(keyword, furniture_data):
    matches = []
    # Simple tokenization matching
    search_terms = keyword.lower().split()
    
    # Synonym map
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

    # 1. Try to infer category from keyword
    target_category = None
    for term in search_terms:
        # Strip punctuation
        clean_term = term.strip(".,")
        if clean_term in category_map:
            target_category = category_map[clean_term]
            break

    for item in furniture_data:
        # Match Logic 1: Category match
        if target_category and item['category'] == target_category:
            matches.append(item)
            continue

        # Match Logic 2: Text match
        item_text = (item['name'] + " " + item['description']).lower()
        
        # Simple match: entire keyword phrase in text
        if keyword in item_text:
            matches.append(item)
            continue
            
        # Fallback match: specific terms in name
        for term in search_terms:
            clean_term = term.strip(".,")
            if len(clean_term) > 3 and clean_term in item['name'].lower():
                matches.append(item)
                break
    
    # Deduplicate
    unique_matches = []
    seen_ids = set()
    for m in matches:
        if m['id'] not in seen_ids:
            unique_matches.append(m)
            seen_ids.add(m['id'])
            
    return unique_matches

def main():
    if not configure_genai():
        return

    # Assume user provides an image path
    # image_path = "test_room.jpg" 
    
    print("Please enter image path (e.g., bedroom.jpg):")
    image_path = input().strip()
    
    # Remove quotes
    image_path = image_path.replace("'", "").replace('"', "")

    print(f"\nAnalyzing image: {image_path} ...")
    recommended_keyword = analyze_and_recommend(image_path)

    if recommended_keyword:
        print(f"AI Suggested Keyword: [{recommended_keyword}]")
        
        furniture_data = load_furniture_data()
        recommendations = find_matching_products(recommended_keyword, furniture_data)
        
        if recommendations:
            print(f"\nWayfair Recommendations (Found {len(recommendations)}):")
            for item in recommendations:
                print(f"- {item['name']} ({item['category']}) - ${item['price']}")
                print(f"  Description: {item['description']}")
        else:
            print(f"\nSorry, no matching items found for '{recommended_keyword}'.")
            print("Try updating furniture_db.json or using a different image.")
    else:
        print("Could not get recommendation keyword.")

if __name__ == "__main__":
    main()
