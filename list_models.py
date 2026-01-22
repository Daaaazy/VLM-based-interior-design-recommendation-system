import google.generativeai as genai

API_KEY = "AIzaSyDdm1ljRHMWoa0FIwqsv3S7tevpCGBrDec"
genai.configure(api_key=API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
