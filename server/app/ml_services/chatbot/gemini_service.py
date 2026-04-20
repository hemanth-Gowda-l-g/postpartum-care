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

Strictly stay within postpartum care, maternal health, lactation, infant care, nutrition, and mental health. Do NOT generate or explain computer code, algorithms, or software development tasks. If the user requests programming/code or other non-health topics, politely refuse and redirect to health topics. Provide a helpful, accurate, and empathetic answer. Always prioritize safety and recommend consulting healthcare providers for serious medical concerns."""
        else:
            prompt = f"""You are a healthcare assistant specializing in postpartum care and baby development.

Question: {query}

Strictly stay within postpartum care, maternal health, lactation, infant care, nutrition, and mental health. Do NOT generate or explain computer code, algorithms, or software development tasks. If the user requests programming/code or other non-health topics, politely refuse and redirect to health topics. Provide a helpful, accurate, and empathetic answer about postpartum care, baby development, or maternal health. Always prioritize safety and recommend consulting healthcare providers for serious medical concerns."""
        
        return {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,  # Lower temperature for medical accuracy
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 300
            }
        }
        
    def get_response(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get response from Gemini API
        Args:
            query: User's question
            context: Optional context to help with the response
        Returns:
            Dict containing the response and metadata
        """
        if not self.api_key:
            return {
                "error": "Gemini API key not configured",
                "answer": "I'm sorry, my AI service is not properly configured right now."
            }
        
        for attempt in range(self.max_retries):
            try:
                # Format the payload for Gemini
                payload = self._format_gemini_payload(query, context)
                
                print(f"🔄 Calling Gemini API (attempt {attempt + 1}/{self.max_retries})")
                
                # Make API request
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract the generated text from Gemini response
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            answer = candidate["content"]["parts"][0]["text"].strip()
                            
                            print("✅ Gemini API call successful")
                            return {
                                "answer": answer,
                                "source": "gemini",
                                "confidence": 0.95  # Gemini is generally very reliable
                            }
                    
                    print(f"❌ Unexpected Gemini response format: {result}")
                    return {
                        "error": "Invalid response format from Gemini API",
                        "answer": "I received an unexpected response format. Please try again."
                    }
                
                elif response.status_code == 400:
                    print(f"❌ Bad request to Gemini API: {response.text}")
                    return {
                        "error": f"Bad request to Gemini API: {response.status_code}",
                        "answer": "I'm having trouble understanding your request. Please try rephrasing your question."
                    }
                
                elif response.status_code == 403:
                    print(f"❌ Gemini API access forbidden: {response.text}")
                    return {
                        "error": f"Gemini API access forbidden: {response.status_code}",
                        "answer": "I'm having trouble accessing my AI service. Please try again later."
                    }
                
                else:
                    print(f"❌ Gemini API error {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    
                    return {
                        "error": f"Gemini API error: {response.status_code}",
                        "answer": "I'm experiencing technical difficulties. Please try again in a few moments."
                    }
                
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout calling Gemini API, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
            
            except Exception as e:
                print(f"❌ Error calling Gemini API (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                
                return {
                    "error": f"Error calling Gemini API: {str(e)}",
                    "answer": "I'm experiencing technical difficulties. Please try again in a few moments."
                }
        
        # If we get here, all attempts failed
        print("❌ All Gemini API attempts failed")
        return {
            "error": "Failed to get response from Gemini after multiple attempts",
            "answer": "I'm sorry, I'm having trouble connecting to my AI service right now. Please try again in a few moments."
        }

# Create a singleton instance
REDACTEDservice = GeminiService()
