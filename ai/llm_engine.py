import os
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Base class cho LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response từ prompt"""
        pass
    
    @abstractmethod
    def generate_structured(self, prompt: str, schema: Dict) -> Dict:
        """Generate structured response (JSON)"""
        pass


class GeminiLLM(BaseLLM):
    """Google Gemini LLM integration"""
    
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-pro"):
        """
        Khởi tạo Gemini LLM
        
        Args:
            api_key: Google API key (nếu None, lấy từ env var GEMINI_API_KEY)
            model: Model name (default: gemini-1.5-pro)
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Cài đặt: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Cần GEMINI_API_KEY environment variable hoặc api_key parameter")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
    
    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """
        Generate response từ prompt
        
        Args:
            prompt: Input prompt
            temperature: Creativity (0-1)
            
        Returns:
            Generated text
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                )
            )
            return response.text
        except Exception as e:
            print(f"Lỗi Gemini: {e}")
            return ""
    
    def generate_structured(self, prompt: str, schema: Dict = None, **kwargs) -> Dict:
        """
        Generate structured response (JSON)
        
        Args:
            prompt: Input prompt
            schema: JSON schema (optional)
            
        Returns:
            Parsed JSON dict
        """
        if schema:
            prompt += f"\n\nOutput JSON format: {json.dumps(schema)}"
        
        response_text = self.generate(prompt, **kwargs)
        
        try:
            # Extract JSON từ response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response_text}
        except json.JSONDecodeError:
            return {"raw_response": response_text}


class GroqLLM(BaseLLM):
    """Groq LLM integration (Llama 3)"""
    
    def __init__(self, api_key: str = None, model: str = "llama3-70b-8192"):
        """
        Khởi tạo Groq LLM
        
        Args:
            api_key: Groq API key (nếu None, lấy từ env var GROQ_API_KEY)
            model: Model name (default: llama3-70b-8192)
        """
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("Cài đặt: pip install groq")
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Cần GROQ_API_KEY environment variable hoặc api_key parameter")
        
        self.client = Groq(api_key=self.api_key)
        self.model_name = model
    
    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """
        Generate response từ prompt
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Lỗi Groq: {e}")
            return ""
    
    def generate_structured(self, prompt: str, schema: Dict = None, **kwargs) -> Dict:
        """Generate structured response (JSON)"""
        if schema:
            prompt += f"\n\nOutput JSON format: {json.dumps(schema)}"
        
        response_text = self.generate(prompt, **kwargs)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response_text}
        except json.JSONDecodeError:
            return {"raw_response": response_text}


class LocalLLM(BaseLLM):
    """Local LLM integration (Ollama)"""
    
    def __init__(self, model: str = "llama3:70b", base_url: str = "http://localhost:11434"):
        """
        Khởi tạo Local LLM (Ollama)
        
        Args:
            model: Model name (default: llama3:70b)
            base_url: Ollama API URL
        """
        try:
            import requests
        except ImportError:
            raise ImportError("Cài đặt: pip install requests")
        
        self.model = model
        self.base_url = base_url
        self.requests = requests
    
    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """Generate response từ local model"""
        try:
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 2048,
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"Lỗi Local LLM: {e}")
            return ""
    
    def generate_structured(self, prompt: str, schema: Dict = None, **kwargs) -> Dict:
        """Generate structured response"""
        if schema:
            prompt += f"\n\nOutput JSON format: {json.dumps(schema)}"
        
        response_text = self.generate(prompt, **kwargs)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response_text}
        except json.JSONDecodeError:
            return {"raw_response": response_text}


class LLMFactory:
    """Factory để tạo LLM instance"""
    
    @staticmethod
    def create(provider: str = "gemini", **kwargs) -> BaseLLM:
        """
        Tạo LLM instance
        
        Args:
            provider: 'gemini', 'groq', 'local'
            **kwargs: Additional arguments cho LLM
            
        Returns:
            LLM instance
        """
        providers = {
            "gemini": GeminiLLM,
            "groq": GroqLLM,
            "local": LocalLLM,
        }
        
        if provider not in providers:
            raise ValueError(f"Provider không hỗ trợ: {provider}. Options: {list(providers.keys())}")
        
        return providers[provider](**kwargs)


if __name__ == "__main__":
    # Test
    print("=== Test LLM Engine ===\n")
    
    # Test Gemini (nếu có API key)
    try:
        gemini = LLMFactory.create("gemini")
        print("Test Gemini...")
        response = gemini.generate("Hello! Say hi back in Vietnamese.")
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Gemini test skipped: {e}\n")
    
    # Test Groq (nếu có API key)
    try:
        groq = LLMFactory.create("groq")
        print("Test Groq...")
        response = groq.generate("Hello! Say hi back in Vietnamese.")
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Groq test skipped: {e}\n")
    
    # Test Local (nếu Ollama đang chạy)
    try:
        local = LLMFactory.create("local", model="llama3:8b")
        print("Test Local LLM...")
        response = local.generate("Hello! Say hi back in Vietnamese.")
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Local LLM test skipped: {e}\n")
