# RAG Chatbot with Hugging Face Fallback

## Overview

This chatbot system implements a hybrid approach combining:
- **RAG (Retrieval-Augmented Generation)** for high-confidence responses from curated postpartum care knowledge
- **Hugging Face API fallback** for queries outside the knowledge base when confidence is below 0.6

## Features

### Core Functionality
- **Smart Response Selection**: Automatically chooses between RAG and HF based on confidence scores
- **Confidence Threshold**: Configurable threshold (default: 0.6) for fallback decisions
- **Context-Aware**: HF responses include relevant context from similar RAG questions
- **Fallback Chain**: Multiple HF models for reliability
- **Chat History**: Persistent conversation storage in MongoDB

### Technical Implementation
- **Sentence Transformers**: Uses `all-MiniLM-L6-v2` for semantic similarity
- **FAISS Index**: Fast similarity search with normalized embeddings
- **Hugging Face Models**: 
  - Primary: `microsoft/DialoGPT-medium`
  - Fallback: `facebook/blenderbot-400M-distill`
- **Confidence Scoring**: Cosine similarity-based confidence calculation

## Setup

### 1. Install Dependencies
```bash
cd server/
pip install -r requirements.txt
```

### 2. Configure Hugging Face API
Create a `.env` file in the server directory:
```bash
# .env
HF_TOKEN=your_huggingface_api_key_here
```

Get your API key from: https://huggingface.co/settings/tokens

### 3. Test the System
```bash
cd server/
python test_chatbot.py
```

## API Endpoints

### Initialize Chatbot
```bash
POST /api/chatbot/initialize
Authorization: Bearer <jwt_token>
```
Initializes the RAG system and loads QA pairs.

### Send Message
```bash
POST /api/chatbot/chat
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "What are the signs of postpartum depression?",
  "chatId": "optional_existing_chat_id"
}
```

### Check Status
```bash
GET /api/chatbot/status
Authorization: Bearer <jwt_token>
```

### Update Settings
```bash
POST /api/chatbot/settings
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "similarity_threshold": 0.7,
  "use_hf_fallback": true
}
```

## How It Works

### 1. Query Processing
1. User sends a question
2. System encodes the question using sentence transformers
3. Searches for similar questions in the FAISS index

### 2. Confidence Calculation
- **High Confidence (≥0.6)**: Uses RAG response from curated knowledge
- **Low Confidence (<0.6)**: Triggers Hugging Face fallback

### 3. Fallback Logic
1. **Primary HF Model**: Tries DialoGPT-medium first
2. **Fallback HF Model**: Falls back to BlenderBot if primary fails
3. **Context Enhancement**: Includes similar RAG questions as context
4. **Response Validation**: Ensures answer quality before returning

### 4. Response Selection
- **RAG Response**: Direct answer from knowledge base
- **HF Response**: AI-generated answer with context
- **Error Handling**: Graceful degradation if both systems fail

## Configuration

### Confidence Threshold
- **Default**: 0.6 (60%)
- **Range**: 0.0 to 1.0
- **Lower values**: More aggressive HF fallback
- **Higher values**: More conservative, prefer RAG

### HF Fallback
- **Enable/Disable**: Toggle HF fallback on/off
- **Model Selection**: Primary and fallback models
- **Retry Logic**: Configurable retry attempts and delays

## Knowledge Base

The RAG system uses a curated dataset of postpartum care Q&A pairs:
- **Source**: `postpartum_qa.json`
- **Topics**: Depression, nutrition, fatigue, hair loss, mastitis, pain management, exercise, skin-to-skin contact, sleep, warning signs
- **Quality**: Medical accuracy verified, postpartum-specific content

## Testing

### Manual Testing
```bash
# Test RAG service
python -c "
from app.ml_services.chatbot.rag_service import rag_service
rag_service.initialize()
response = rag_service.get_response('What are signs of PPD?')
print(response)
"
```

### Automated Testing
```bash
python test_chatbot.py
```

## Troubleshooting

### Common Issues

1. **RAG Initialization Fails**
   - Check if `postpartum_qa.json` exists
   - Verify sentence-transformers installation
   - Check FAISS compatibility

2. **HF API Errors**
   - Verify `HF_TOKEN` in `.env`
   - Check API key validity
   - Monitor rate limits

3. **Low Confidence Responses**
   - Adjust similarity threshold
   - Expand knowledge base
   - Review embedding model

4. **Performance Issues**
   - Reduce FAISS index size
   - Optimize embedding model
   - Cache frequent queries

### Debug Mode
Enable verbose logging in the services:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Metrics

### Response Times
- **RAG Only**: ~50-100ms
- **HF Fallback**: ~200-500ms
- **Error Fallback**: ~100-200ms

### Accuracy
- **RAG Responses**: High accuracy for covered topics
- **HF Responses**: Variable accuracy, context-dependent
- **Overall System**: Graceful degradation under load

## Future Enhancements

1. **Dynamic Thresholds**: Adaptive confidence thresholds based on query type
2. **Model Fine-tuning**: Custom models for postpartum care domain
3. **Feedback Loop**: User rating system for response quality
4. **Multi-language Support**: International postpartum care knowledge
5. **Real-time Updates**: Live knowledge base updates

## Security Considerations

- **API Key Protection**: Store HF_TOKEN securely
- **Input Validation**: Sanitize user queries
- **Rate Limiting**: Implement API call limits
- **Content Filtering**: Filter inappropriate responses
- **User Privacy**: Secure chat history storage

## Support

For issues or questions:
1. Check the test script output
2. Review server logs for error messages
3. Verify API key configuration
4. Test individual components separately
