import json
import random
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def generate_furniture_data():
    categories = [
        "Rugs", "Lamps", "Chairs", "Wall Art", "Pillows"
    ]
    
    # Pre-defining some realistic base items to ensure variety and quality names
    base_items = {
        "Rugs": [
            ("Moroccan Diamond Rug", 129.99),
            ("Vintage Distressed Area Rug", 199.50),
            ("Faux Fur Sheepskin Rug", 45.00),
            ("Jute Braided Runner", 55.99)
        ],
        "Lamps": [
            ("Industrial Tripod Floor Lamp", 149.99),
            ("Modern Ceramic Table Lamp", 65.00),
            ("Geometric Pendant Light", 89.99),
            ("Adjustable Desk Lamp", 42.50)
        ],
        "Chairs": [
            ("Velvet Accent Armchair", 299.00),
            ("Mid-Century Dining Chair", 110.00),
            ("Leather Recliner", 450.00),
            ("Rattan Lounge Chair", 185.00)
        ],
        "Wall Art": [
            ("Abstract Canvas Print", 75.00),
            ("Botanical Framed Set", 120.00),
            ("Minimalist Line Drawing", 45.00),
            ("Coastal Landscape Photo", 85.00)
        ],
        "Pillows": [
            ("Boho Tassel Throw Pillow", 35.00),
            ("Velvet Lumbar Cushion", 28.50),
            ("Geometric Print Pillow", 32.00),
            ("Knitted Cotton Pillow", 40.00)
        ]
    }

    styles = [
        "Modern", "Rustic", "Bohemian", "Industrial", "Scandi", 
        "Traditional", "Contemporary", "Farmhouse"
    ]

    furniture_list = []
    current_id = 1

    # Ensure we cover all categories by iterating through our base items
    # Each category has 4 items, 5 categories * 4 = 20 total items.
    for category, items in base_items.items():
        for name, base_price in items:
            # Add some slight variation to price or keep valid float
            price = base_price
            
            style = random.choice(styles)
            
            # Extract last word from name for keyword (e.g., 'Sofa' from 'Mid-Century Modern Sofa')
            keyword = name.split()[-1]
            
            # Generate random image URL
            image_url = f"https://loremflickr.com/400/300/{keyword}?random={random.randint(1, 10000)}"
            
            item = {
                "id": current_id,
                "name": name,
                "category": category,
                "style": style,
                "description": f"A beautiful {style.lower()} style {name.lower()} that adds character to any room. Perfect for upgrading your home decor.",
                "price": price,
                "image_url": image_url
            }
            furniture_list.append(item)
            current_id += 1

    return furniture_list

def generate_embeddings(furniture_data, output_index="furniture_vectors.index"):
    print("Loading Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    texts = []
    for item in furniture_data:
        # Construct a rich descriptive text for embedding
        text = f"{item['name']} {item['style']} {item['category']} {item['description']}"
        texts.append(text)
    
    print("Computing embeddings...")
    embeddings = model.encode(texts)
    
    # FAISS expects numpy float32 array
    embeddings = np.array(embeddings).astype('float32')
    
    # Dimension of the embeddings (all-MiniLM-L6-v2 outputs 384 dimensions)
    d = embeddings.shape[1] 
    
    print(f"Creating FAISS index (dimension={d})...")
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    
    faiss.write_index(index, output_index)
    print(f"Saved FAISS index to {output_index}")

if __name__ == "__main__":
    data = generate_furniture_data()
    
    output_file = "furniture_db.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully generated {len(data)} items in {output_file}.")
    
    # Generate vectors
    generate_embeddings(data)
