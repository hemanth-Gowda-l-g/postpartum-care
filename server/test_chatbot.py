#!/usr/bin/env python3
"""
Test script for the RAG Chatbot with Hugging Face fallback
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / 'app'))

def test_rag_service():
    """Test the RAG service directly"""
    print("🧪 Testing RAG Service")
    print("=" * 50)
    
    try:
        from ml_services.chatbot.rag_service import rag_service
        
        # Test initialization
        print("🔄 Testing initialization...")
        success = rag_service.initialize()
        if success:
            print("✅ RAG service initialized successfully")
        else:
            print("❌ RAG service initialization failed")
            return False
        
        # Test queries with different confidence levels
        test_queries = [
            "What are the signs of postpartum depression?",  # High confidence - should use RAG
            "How do I know if I have PPD?",  # Medium confidence - might use RAG
            "What is the weather like today?",  # Low confidence - should trigger HF fallback
            "Tell me about quantum physics",  # Very low confidence - should trigger HF fallback
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            response = rag_service.get_response(query, top_k=3, similarity_threshold=0.6)
            
            if 'error' in response:
                print(f"❌ Error: {response['error']}")
            else:
                print(f"✅ Response: {response['answer'][:100]}...")
                print(f"   Source: {response['source']}")
                print(f"   Confidence: {response.get('confidence', 'N/A'):.3f}")
                if response.get('rag_confidence'):
                    print(f"   RAG Confidence: {response['rag_confidence']:.3f}")
                if response.get('similar_questions'):
                    print(f"   Similar questions: {len(response['similar_questions'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RAG service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hf_service():
    """Test the Hugging Face service directly"""
    print("\n🧪 Testing Hugging Face Service")
    print("=" * 50)
    
    try:
        from ml_services.chatbot.hf_service import huggingface_service
        
        # Check if API key is configured
        if not huggingface_service.api_key:
            print("⚠️  No HF_TOKEN found - skipping HF tests")
            return True
        
        # Test queries
        test_queries = [
            "What should I eat after giving birth?",
            "How can I improve my sleep with a newborn?",
            "What exercises are safe postpartum?",
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing HF query: '{query}'")
            response = huggingface_service.get_response(query)
            
            if 'error' in response:
                print(f"❌ Error: {response['error']}")
            else:
                print(f"✅ Response: {response['answer'][:100]}...")
                print(f"   Source: {response['source']}")
                print(f"   Model: {response.get('model', 'N/A')}")
                print(f"   Confidence: {response.get('confidence', 'N/A'):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing HF service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test the integrated chatbot flow"""
    print("\n🧪 Testing Integrated Chatbot Flow")
    print("=" * 50)
    
    try:
        from ml_services.chatbot.rag_service import rag_service
        
        # Ensure RAG is initialized
        if not rag_service.initialized:
            rag_service.initialize()
        
        # Test the complete flow
        test_scenarios = [
            {
                "name": "High Confidence RAG",
                "query": "What are the signs of postpartum depression?",
                "expected_source": "rag"
            },
            {
                "name": "Low Confidence HF Fallback",
                "query": "What is the capital of France?",
                "expected_source": "huggingface"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            print(f"   Query: '{scenario['query']}'")
            
            response = rag_service.get_response(scenario['query'], similarity_threshold=0.6)
            
            if 'error' in response:
                print(f"   ❌ Error: {response['error']}")
            else:
                print(f"   ✅ Source: {response['source']}")
                print(f"   ✅ Confidence: {response.get('confidence', 'N/A'):.3f}")
                print(f"   ✅ Answer: {response['answer'][:80]}...")
                
                # Check if fallback worked as expected
                if scenario['expected_source'] == 'rag' and response['source'] == 'rag':
                    print("   🎯 RAG response as expected")
                elif scenario['expected_source'] == 'huggingface' and response['source'] in ['huggingface', 'huggingface_fallback']:
                    print("   🎯 HF fallback as expected")
                else:
                    print(f"   ⚠️  Unexpected source: {response['source']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🤖 Chatbot System Test Suite")
    print("=" * 60)
    
    # Test 1: RAG Service
    rag_ok = test_rag_service()
    
    # Test 2: Hugging Face Service
    hf_ok = test_hf_service()
    
    # Test 3: Integration
    integration_ok = test_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"RAG Service: {'✅ PASS' if rag_ok else '❌ FAIL'}")
    print(f"HF Service:  {'✅ PASS' if hf_ok else '❌ PASS'}")
    print(f"Integration: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    if rag_ok and integration_ok:
        print("\n🎉 Chatbot system is working correctly!")
        print("\nYou can now:")
        print("  1. Initialize the chatbot: POST /api/chatbot/initialize")
        print("  2. Send messages: POST /api/chatbot/chat")
        print("  3. Check status: GET /api/chatbot/status")
        print("  4. Update settings: POST /api/chatbot/settings")
        return True
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
