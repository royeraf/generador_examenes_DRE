import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

async def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = await model.generate_content_async("Hola, dime 1+1")
        print(f"SUCCESS {model_name}: {response.text}")
    except Exception as e:
        print(f"FAILED {model_name}: {e}")

async def main():
    models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest', 'gemini-3-flash-preview']
    for m in models:
        await test_model(m)

if __name__ == "__main__":
    asyncio.run(main())
