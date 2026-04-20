import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Any
from .gemini_service import REDACTEDservice

class RAGChatbotService:
    def __init__(self):
        self.encoder = None
        self.index = None
        self.qa_pairs = None
        self.initialized = False
        self.use_gemini_fallback = True  # Whether to use Gemini as fallback
        self.similarity_threshold = 0.7  # Higher threshold for better accuracy
        
    def initialize(self, model_name: str = "all-MiniLM-L6-v2", force: bool = False):
        """Initialize the RAG chatbot with the specified model.

        If the service is already initialized and `force` is False, this will
        short-circuit and return True immediately to avoid reloading large
        models and rebuilding the FAISS index on every `/initialize` request.
        """
        # Short-circuit if already initialized (prevents repeated heavy loads)
        if self.initialized and not force:
            print("ℹ️ RAG chatbot already initialized (skipping)")
            return True

        try:
            print("🔄 Initializing RAG chatbot...")

            # Initialize the sentence transformer
            self.encoder = SentenceTransformer(model_name)
            print(f"✅ Sentence transformer loaded: {model_name}")

            # Load the QA pairs
            qa_path = os.path.join(os.path.dirname(__file__), 'postpartum_qa.json')
            with open(qa_path, 'r', encoding='utf-8') as f:
                self.qa_pairs = json.load(f)
            print(f"✅ Loaded {len(self.qa_pairs)} QA pairs")

            # Create embeddings for all questions
            questions = [pair['question'] for pair in self.qa_pairs]
            question_embeddings = self.encoder.encode(questions, convert_to_numpy=True)

            # Normalize embeddings for better similarity calculation
            faiss.normalize_L2(question_embeddings)

            # Create FAISS index using cosine similarity (L2 distance for normalized vectors)
            self.index = faiss.IndexFlatL2(question_embeddings.shape[1])  # L2 distance for normalized vectors = cosine distance
            self.index.add(question_embeddings)

            self.initialized = True
            print("✅ RAG chatbot initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Error initializing RAG chatbot: {str(e)}")
            return False
    
    def get_response(self, query: str, top_k: int = 3, similarity_threshold: float = None) -> Dict[str, Any]:
        """Get response for a user query using RAG with Hugging Face fallback"""
        if not self.initialized:
            return {"error": "Chatbot not initialized"}
        
        # Use instance threshold if none provided
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        try:
            # Encode the query
            query_embedding = self.encoder.encode([query], convert_to_numpy=True)
            
            # Normalize query embedding
            faiss.normalize_L2(query_embedding)

            # Search for similar questions using L2 distance (cosine distance for normalized vectors)
            distances, indices = self.index.search(query_embedding, top_k)

            # Calculate confidence score from L2 distance
            # For normalized vectors, L2 distance ranges from 0 (identical) to 2 (opposite)
            # Convert to confidence: 0 distance = 1.0 confidence, 2 distance = 0.0 confidence
            raw_distance = float(distances[0][0])
            confidence = max(0.0, 1.0 - (raw_distance / 2.0))

            # Get the best matching question for debugging
            best_match_idx = indices[0][0]
            best_question = self.qa_pairs[best_match_idx]['question']

            print(f"🔍 Query: '{query}'")
            print(f"🔍 Best match: '{best_question}'")
            print(f"🔍 Raw distance: {raw_distance:.4f}, Confidence: {confidence:.3f}, Threshold: {similarity_threshold}")
            
            # If confidence is below threshold, try Gemini fallback
            if confidence < similarity_threshold and self.use_gemini_fallback:
                print(f"🔄 Confidence {confidence:.3f} below threshold {similarity_threshold}, trying Gemini fallback")

                # Get context from similar questions for better Gemini response
                context = "\n".join([
                    f"Q: {self.qa_pairs[idx]['question']}\nA: {self.qa_pairs[idx]['answer']}"
                    for idx in indices[0]
                ])

                gemini_response = REDACTEDservice.get_response(query, context)
                if "error" not in gemini_response:
                    print(f"✅ Gemini fallback successful")
                    return {
                        "answer": gemini_response["answer"],
                        "confidence": gemini_response.get("confidence", 0.95),  # Gemini confidence
                        "source": "gemini",
                        "rag_confidence": confidence,  # Keep RAG confidence for reference
                        "similar_questions": [
                            {
                                "question": self.qa_pairs[idx]['question'],
                                "answer": self.qa_pairs[idx]['answer']
                            }
                            for idx in indices[0]
                        ]
                    }
                else:
                    print(f"❌ Gemini fallback failed: {gemini_response.get('error')}")
                    print(f"🔄 Falling back to RAG response")

            # If we're here, either confidence is good or Gemini failed, so use RAG response
            best_match_idx = indices[0][0]
            best_match = self.qa_pairs[best_match_idx]
            
            print(f"✅ Using RAG response with confidence {confidence:.3f}")
            
            return {
                "answer": best_match['answer'],
                "confidence": confidence,
                "source": "rag",
                "similar_questions": [
                    {
                        "question": self.qa_pairs[idx]['question'],
                        "answer": self.qa_pairs[idx]['answer']
                    }
                    for idx in indices[0][1:]  # Exclude the best match
                ]
            }
            
        except Exception as e:
            print(f"❌ Error in RAG service: {str(e)}")
            # If RAG fails, try Hugging Face as last resort
            if self.use_hf_fallback:
                print("🔄 Attempting Hugging Face fallback due to RAG error")
                try:
                    hf_response = self.hf_service.get_response(query)
                    if "error" not in hf_response:
                        print("✅ Hugging Face fallback successful after RAG error")
                        return {
                            "answer": hf_response["answer"],
                            "confidence": hf_response.get("confidence", 0.6),
                            "source": "huggingface_fallback",
                            "rag_error": str(e)
                        }
                except Exception as hf_error:
                    print(f"❌ Hugging Face fallback also failed: {str(hf_error)}")
            
            return {"error": f"Error processing query: {str(e)}"}

# Create a singleton instance
rag_service = RAGChatbotService() 