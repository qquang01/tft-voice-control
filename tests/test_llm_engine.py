"""
Test script cho LLM Engine
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_engine import LLMFactory


def test_llm_engine():
    print("=== Test LLM Engine ===\n")
    
    # Test Gemini
    print("1. Test Gemini (cần GEMINI_API_KEY)...")
    try:
        gemini = LLMFactory.create("gemini")
        response = gemini.generate("Say 'Hello' in Vietnamese.")
        print(f"✓ Gemini response: {response}\n")
    except Exception as e:
        print(f"✗ Gemini test skipped: {e}\n")
    
    # Test Groq
    print("2. Test Groq (cần GROQ_API_KEY)...")
    try:
        groq = LLMFactory.create("groq")
        response = groq.generate("Say 'Hello' in Vietnamese.")
        print(f"✓ Groq response: {response}\n")
    except Exception as e:
        print(f"✗ Groq test skipped: {e}\n")
    
    # Test Local
    print("3. Test Local LLM (cần Ollama đang chạy)...")
    try:
        local = LLMFactory.create("local", model="llama3:8b")
        response = local.generate("Say 'Hello' in Vietnamese.")
        print(f"✓ Local response: {response}\n")
    except Exception as e:
        print(f"✗ Local test skipped: {e}\n")
    
    # Test structured output
    print("4. Test structured output...")
    try:
        gemini = LLMFactory.create("gemini")
        schema = {
            "action": "string",
            "target": "string",
            "confidence": "float"
        }
        response = gemini.generate_structured(
            "Recommend buying Ahri in TFT. Output in JSON.",
            schema
        )
        print(f"✓ Structured response: {response}\n")
    except Exception as e:
        print(f"✗ Structured test skipped: {e}\n")
    
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_llm_engine()
