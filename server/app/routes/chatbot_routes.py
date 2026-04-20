from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from ..ml_services.chatbot.rag_service import rag_service
from ..ml_services.chatbot.gemini_service import REDACTEDservice
from ..ml_services.sentiment import analyze_sentiment
from ..utils.database import mongo
from datetime import datetime
from bson import ObjectId

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/initialize', methods=['POST', 'OPTIONS'])
@cross_origin()
@jwt_required()
def initialize_chatbot():
    """Initialize the RAG chatbot"""
    if request.method == 'OPTIONS':
        return '', 200
    try:
        # If already initialized, short-circuit to avoid reloading models
        success = rag_service.initialize()
        if success:
            return jsonify({
                "message": "Chatbot initialized successfully",
                "features": {
                    "rag": True,
                    "huggingface": True,
                    "confidence_threshold": rag_service.similarity_threshold
                }
            }), 200
        else:
            return jsonify({"error": "Failed to initialize RAG chatbot"}), 500
    except Exception as e:
        print(f"❌ Error initializing chatbot: {str(e)}")
        return jsonify({"error": f"Initialization error: {str(e)}"}), 500

@chatbot_bp.route('/chat', methods=['POST', 'OPTIONS'])
@cross_origin()
@jwt_required()
def chat():
    """Handle chat messages with both RAG and Hugging Face support, and store chat history."""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
        
        user_message = data['message']
        print(f"💬 User message: {user_message}")

        # --- Safety guardrails: detect harm to self/others and de-escalate with emergency guidance ---
        def _is_harm_intent(msg: str) -> bool:
            if not isinstance(msg, str):
                return False
            m = msg.lower()
            harm_terms = [
                'kill', 'murder', 'hurt', 'harm', 'stab', 'shoot', 'poison', 'beat', 'attack',
                'suicide', 'kill myself', 'end my life', 'self harm', 'self-harm', 'hurt myself'
            ]
            # simple heuristic: presence of a harm term with a target or self reference
            return any(t in m for t in harm_terms)

        if _is_harm_intent(user_message):
            deescalate = (
                "I’m really sorry you’re feeling this way. I can’t help with harming anyone. "
                "Please do not do this. If you or someone is in immediate danger, call your local emergency number right now. "
                "You deserve support—consider contacting a crisis hotline or a mental health professional immediately. "
                "If you can, reach out to a trusted person or your doctor/midwife for help."
            )
            response = {
                'answer': deescalate,
                'confidence': 1.0,
                'source': 'safety',
                'similar_questions': []
            }
        else:
            # --- Simple scope guardrails: refuse code-generation and developer-tooling requests ---
            def _is_code_generation(msg: str) -> bool:
                if not isinstance(msg, str):
                    return False
                m = msg.lower()
                code_lang_terms = [
                    'c++', 'cpp', 'c#', 'python', 'java', 'javascript', 'typescript', 'go ', 'golang', 'rust', 'kotlin',
                    'swift', 'ruby', 'php', 'sql', 'html', 'css', 'bash', 'shell', 'powershell'
                ]
                code_signals = [
                    '#include', 'int main(', 'public static void main', 'console.log(', 'def ', 'class ', 'function ',
                    'SELECT *', 'INSERT INTO', 'CREATE TABLE', '<!doctype', '<html', '</html>', 'npm install', 'pip install'
                ]
                code_intents = [
                    'write code', 'generate code', 'code for', 'program for', 'script for', 'algorithm for',
                    'build an app', 'create a website', 'leetcode', 'hackerrank'
                ]
                return (
                    any(term in m for term in code_lang_terms) or
                    any(sig in m for sig in code_signals) or
                    any(intent in m for intent in code_intents)
                )

            if _is_code_generation(user_message):
                safe_msg = (
                    "I’m here to help with postpartum recovery, infant care, lactation, nutrition, mental health, and when to seek medical care. "
                    "Please don’t use this assistant for programming or software tasks. Ask a health-related question instead."
                )
                response = {
                    'answer': safe_msg,
                    'confidence': 1.0,
                    'source': 'guardrails',
                    'similar_questions': []
                }
            else:
                # Get response from RAG service (which may use Hugging Face as fallback)
                response = rag_service.get_response(
                    user_message,
                    top_k=3,
                    similarity_threshold=0.6
                )
        
        if 'error' in response:
            print(f"❌ RAG service error: {response['error']}")
            return jsonify(response), 500
        
        # Add metadata about the response source
        response['metadata'] = {
            'source': response.get('source', 'unknown'),
            'confidence': response.get('confidence', 0.0),
            'has_similar_questions': bool(response.get('similar_questions')),
            'timestamp': datetime.utcnow().isoformat()
        }

        # --- Chat history storage logic ---
        user_id = get_jwt_identity()
        chat_id = data.get('chatId')
        bot_response = response.get('answer', response.get('response', ''))
        now = datetime.utcnow()

        try:
            if chat_id:
                # Append to existing chat
                mongo.db.chats.update_one(
                    {'_id': ObjectId(chat_id), 'user_id': user_id},
                    {'$push': {'messages': [
                        {
                            'sender': 'user',
                            'text': user_message,
                            'timestamp': now,
                            'sentiment': analyze_sentiment(user_message)
                        },
                        {'sender': 'bot', 'text': bot_response, 'timestamp': now}
                    ]}}
                )
                print(f"✅ Updated existing chat: {chat_id}")
            else:
                # Create new chat session
                chat_doc = {
                    'user_id': user_id,
                    'created_at': now,
                    'messages': [
                        {
                            'sender': 'user',
                            'text': user_message,
                            'timestamp': now,
                            'sentiment': analyze_sentiment(user_message)
                        },
                        {'sender': 'bot', 'text': bot_response, 'timestamp': now}
                    ]
                }
                result = mongo.db.chats.insert_one(chat_doc)
                chat_id = str(result.inserted_id)
                print(f"✅ Created new chat: {chat_id}")

            response['chatId'] = str(chat_id)
            
        except Exception as db_error:
            print(f"⚠️  Database error (continuing without chat history): {str(db_error)}")
            # Continue without chat history if there's a DB error
            response['chatId'] = None

        print(f"✅ Chat response generated successfully")
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        return jsonify({"error": f"Chat error: {str(e)}"}), 500

@chatbot_bp.route('/chats', methods=['GET'])
@cross_origin()
@jwt_required()
def list_chats():
    """List chat sessions for the authenticated user (most recent first)."""
    try:
        user_id = get_jwt_identity()
        cursor = mongo.db.chats.find({
            'user_id': user_id
        }).sort('created_at', -1)

        chats = []
        for doc in cursor:
            msgs = doc.get('messages', [])
            preview = msgs[0]['text'][:80] + ('…' if msgs and len(msgs[0]['text']) > 80 else '') if msgs else ''
            chats.append({
                'id': str(doc['_id']),
                'created_at': doc.get('created_at'),
                'last_message_at': msgs[-1].get('timestamp') if msgs else doc.get('created_at'),
                'message_count': len(msgs),
                'preview': preview
            })
        return jsonify({'chats': chats}), 200
    except Exception as e:
        print(f"❌ Error listing chats: {str(e)}")
        return jsonify({'error': f'List chats error: {str(e)}'}), 500

@chatbot_bp.route('/chats/<chat_id>', methods=['GET', 'DELETE'])
@cross_origin()
@jwt_required()
def chat_detail(chat_id):
    """Get messages for a chat or delete it (soft delete can be added later)."""
    try:
        user_id = get_jwt_identity()
        try:
            oid = ObjectId(chat_id)
        except Exception:
            return jsonify({'error': 'Invalid chat id'}), 400

        if request.method == 'GET':
            doc = mongo.db.chats.find_one({'_id': oid, 'user_id': user_id})
            if not doc:
                return jsonify({'error': 'Chat not found'}), 404
            messages = doc.get('messages', [])
            # Normalize timestamps to ISO strings
            norm = []
            for m in messages:
                norm.append({
                    'sender': m.get('sender'),
                    'text': m.get('text', ''),
                    'timestamp': m.get('timestamp').isoformat() if isinstance(m.get('timestamp'), datetime) else m.get('timestamp'),
                })
            return jsonify({'chatId': chat_id, 'messages': norm}), 200
        else:  # DELETE
            res = mongo.db.chats.delete_one({'_id': oid, 'user_id': user_id})
            if res.deleted_count == 0:
                return jsonify({'error': 'Chat not found'}), 404
            return jsonify({'message': 'Chat deleted'}), 200
    except Exception as e:
        print(f"❌ Error in chat_detail: {str(e)}")
        return jsonify({'error': f'Chat detail error: {str(e)}'}), 500

@chatbot_bp.route('/settings', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
@jwt_required()
def chatbot_settings():
    """Get or update chatbot settings"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if request.method == 'GET':
            return jsonify({
                "use_gemini_fallback": rag_service.use_gemini_fallback,
                "similarity_threshold": rag_service.similarity_threshold,
                "initialized": rag_service.initialized
            }), 200
        
        elif request.method == 'POST':
            data = request.get_json()
            if data.get('similarity_threshold') is not None:
                rag_service.similarity_threshold = float(data['similarity_threshold'])
            if data.get('use_gemini_fallback') is not None:
                rag_service.use_gemini_fallback = bool(data['use_gemini_fallback'])
            
            return jsonify({
                "message": "Settings updated successfully",
                "use_gemini_fallback": rag_service.use_gemini_fallback,
                "similarity_threshold": rag_service.similarity_threshold
            }), 200
            
    except Exception as e:
        print(f"❌ Error in settings endpoint: {str(e)}")
        return jsonify({"error": f"Settings error: {str(e)}"}), 500

@chatbot_bp.route('/status', methods=['GET'])
@cross_origin()
@jwt_required()
def chatbot_status():
    """Get chatbot status and health"""
    try:
        return jsonify({
            "rag_initialized": rag_service.initialized,
            "gemini_available": bool(REDACTEDservice.api_key),
            "similarity_threshold": rag_service.similarity_threshold,
            "use_gemini_fallback": rag_service.use_gemini_fallback,
            "qa_pairs_loaded": len(rag_service.qa_pairs) if rag_service.qa_pairs else 0
        }), 200
    except Exception as e:
        print(f"❌ Error in status endpoint: {str(e)}")
        return jsonify({"error": f"Status error: {str(e)}"}), 500 