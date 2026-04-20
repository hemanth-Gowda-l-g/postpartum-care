import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Optional
import time
import json

class GeminiService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Using Google Gemini API for medical/healthcare responses
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key}"
        self.headers = {"Content-Type": "application/json"}
        self.max_retries = 3
        self.retry_delay = 1  # seconds

        if not self.api_key:
            print("⚠️  Warning: GEMINI_API_KEY not found in environment variables")
        
    def _format_gemini_payload(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Format the payload for Gemini API"""
        if context:
            prompt = f"""You are a healthcare assistant specializing in postpartum care and baby development. Based on this medical context: {context}

Question: {query}

Please provide a helpful, accurate, and empathetic answer. Always prioritize safety and recommend consulting healthcare providers for serious medical concerns."""
        else:
            prompt = f"""You are a healthcare assistant specializing in postpartum care and baby development.

Question: {query}

Please provide a helpful, accurate, and empathetic answer about postpartum care, baby development, or maternal health. Always prioritize safety and recommend consulting healthcare providers for serious medical concerns."""

        return {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 300
            }
        }

    def get_response(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get response from Hugging Face API with retries and fallback models
        Args:
            query: User's question
            context: Optional context to help with the response
        Returns:
            Dict containing the response and metadata
        """
        if not self.api_key:
            return {
                "error": "Hugging Face API key not configured",
                "answer": "I'm sorry, I'm having trouble connecting to my AI service. Please try again later."
            }
        
        # Try primary model first
        models_to_try = [self.primary_model, self.fallback_model]
        
        for model_idx, model_name in enumerate(models_to_try):
            api_url = f"https://api-inference.huggingface.co/models/{model_name}"
            print(f"🔄 Trying model: {model_name}")
            
            for attempt in range(self.max_retries):
                try:
                    # Format the prompt
                    prompt = self._format_prompt(query, context)
                    
                    # Make API request
                    response = requests.post(
                        api_url,
                        headers=self.headers,
                        json={
                            "inputs": prompt,
                            "parameters": {
                                "max_new_tokens": 150,
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "do_sample": True,
                                "return_full_text": False,
                                "repetition_penalty": 1.1
                            }
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Handle different response formats
                        if isinstance(result, list) and len(result) > 0:
                            answer = result[0].get("generated_text", "").strip()
                        elif isinstance(result, dict):
                            answer = result.get("generated_text", "").strip()
                        else:
                            answer = str(result).strip()
                        
                        # Clean up the response
                        answer = answer.replace("</s>", "").replace("<s>", "").strip()
                        
                        # Validate answer quality
                        if len(answer) > 10 and answer.lower() not in ["", "none", "unknown", "i don't know", "error"]:
                            print(f"✅ Success with {model_name}")
                            return {
                                "answer": answer,
                                "source": "huggingface",
                                "model": model_name,
                                "confidence": 0.8 if model_idx == 0 else 0.7  # Primary model gets higher confidence
                            }
                        else:
                            print(f"⚠️  {model_name} gave insufficient answer: '{answer}'")
                            if attempt < self.max_retries - 1:
                                time.sleep(self.retry_delay)
                                continue
                            else:
                                # Try next model
                                break
                    
                    elif response.status_code == 503:
                        # Model is loading, wait and retry
                        print(f"⏳ Model {model_name} is loading, attempt {attempt + 1}/{self.max_retries}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                            continue
                    
                    elif response.status_code == 404:
                        print(f"❌ Model {model_name} not found")
                        break  # Try next model
                    
                    elif response.status_code == 401:
                        print(f"❌ Unauthorized access to {model_name}")
                        return {
                            "error": "Unauthorized access to Hugging Face API",
                            "answer": "I'm sorry, I'm having authentication issues. Please check your API configuration."
                        }
                    
                    else:
                        print(f"❌ API error {response.status_code} for {model_name}: {response.text}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                
                except requests.exceptions.Timeout:
                    print(f"⏰ Timeout for {model_name}, attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                
                except Exception as e:
                    print(f"❌ Error calling {model_name} API (attempt {attempt + 1}): {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
        
        # If we get here, all models failed
        print("❌ All Hugging Face models failed")
        return {
            "error": "Failed to get response from Hugging Face after multiple attempts",
            "answer": "I'm sorry, I'm having trouble connecting to my AI service right now. Please try again in a few moments."
        }

# Create a singleton instance
REDACTEDservice = HuggingFaceService()