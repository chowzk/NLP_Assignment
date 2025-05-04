# app.py
from flask import Flask, render_template, request, jsonify, Response, g, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from chatbot_convo import get_chatbot_response, conversation_history, client  
import nltk
from extractor import pdf_Extractor
import os
import re
import logging
from textToSpeech import TTS
from pydub import AudioSegment
from pydub.utils import which
import speech_recognition as sr

## Run this for the first time 
# nltk.download('punkt', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('wordnet', quiet=True)
# nltk.download('punkt_tab', quiet=True)

app = Flask(__name__)
tts_instance = TTS()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), default='New Chat')
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    messages = db.relationship('Message', backref='chat', cascade="all, delete-orphan")
    documents = db.relationship('Document', backref='chat', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    cleaned_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# Initialize database and reset extractor state
with app.app_context():
    db.create_all()

# Helper function to generate incremental chat names
def generate_chat_name():
    chats = Chat.query.all()
    existing_names = [chat.name for chat in chats]
    base_name = "New Chat"
    
    if base_name not in existing_names:
        return base_name
    
    # Find the highest suffix
    max_suffix = 0
    for name in existing_names:
        match = re.match(r"New Chat (\d+)", name)
        if match:
            suffix = int(match.group(1))
            max_suffix = max(max_suffix, suffix)
    
    return f"New Chat {max_suffix + 1}"

# if not os.path.exists('temp'):
#     os.makedirs('temp')

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Get all chats for the sidebar
@app.route('/chats', methods=['GET'])
def get_chats():
    chats = Chat.query.order_by(Chat.created_at.desc()).all()
    chat_data = []
    for chat in chats:
        last_message = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.desc()).first()
        last_modified = last_message.timestamp if last_message else chat.created_at
        chat_data.append({
            'id': chat.id,
            'name': chat.name,
            'created_at': chat.created_at.isoformat(),
            'last_modified': last_modified.isoformat()
        })
    return jsonify(chat_data)

# Create a new chat
@app.route('/chats', methods=['POST'])
def create_chat():
    temp_chat_id = f"temp_{datetime.now(timezone.utc).timestamp()}"  # Unique temporary ID
    chat_name = generate_chat_name()  # Generate name but don't save yet
    return jsonify({
        'id': temp_chat_id,
        'name': chat_name,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'temporary': True
    })
    # new_chat = Chat(name='New Chat')
    # db.session.add(new_chat)
    # db.session.commit()
    # return jsonify({'id': new_chat.id, 'name': new_chat.name, 'created_at': new_chat.created_at.isoformat()})

# Get messages for a specific chat
@app.route('/chats/<string:chat_id>', methods=['GET'])
def get_chat_messages(chat_id):
    if chat_id.startswith('temp_'):
        # Return empty messages for temporary chats
        return jsonify([])
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        return jsonify({'error': 'Invalid chat ID'}), 400
    chat = Chat.query.get_or_404(chat_id_int)
    messages = Message.query.filter_by(chat_id=chat_id_int).order_by(Message.timestamp.asc()).all()
    return jsonify([{
        'role': msg.role,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages])

# Update chat name
@app.route('/chats/<int:chat_id>', methods=['PUT'])
def update_chat_name(chat_id):
    data = request.json
    chat = Chat.query.get_or_404(chat_id)
    if 'name' in data:
        chat.name = data['name']
        db.session.commit()
    return jsonify({
        'id': chat.id,
        'name': chat.name,
        'created_at': chat.created_at.isoformat()
    })
    # data = request.json
    # new_name = data.get('name')
    # if not new_name:
    #     return jsonify({'error': 'Name is required'}), 400
    # chat = Chat.query.get_or_404(chat_id)
    # chat.name = new_name
    # db.session.commit()
    # return jsonify({'id': chat.id, 'name': chat.name})

# # Route for the form page
# @app.route('/form', methods=['GET', 'POST'])
# def form():
#     if request.method == 'POST':
#         name = request.form['name']
#         return render_template('form.html', message=f'Hello, {name}!')
#     return render_template('form.html', message='Please enter your name.')

# Delete a chat
@app.route('/chats/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chat = Chat.query.get(chat_id)
    if chat is None:
        return jsonify({'error': 'Chat not found'}), 404
    db.session.delete(chat)
    db.session.commit()
    logger.info(f"Deleted chat with id: {chat_id}")
    return '', 204

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    chat_id = data.get('chat_id')
    user_input = data.get('message')

    if not chat_id or not user_input:
        return jsonify({'error': 'chat_id and message are required'}), 400
    chat_id_str = str(chat_id)  # Convert chat_id to string
    if chat_id_str.startswith('temp_'):
        return jsonify({'error': 'Cannot ask questions in a temporary chat. Please upload a document first.'}), 400
    try:
        chat_id_int = int(chat_id_str)
    except ValueError:
        return jsonify({'error': 'Invalid chat ID'}), 400
    chat = db.session.get(Chat, chat_id_int)
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    # Check if the query is relevant
    success, message = pdf_Extractor.is_query_relevant(db,user_input)
    if not success:
        return jsonify({'error': message}), 400

    messages = Message.query.filter_by(chat_id=chat_id_int).order_by(Message.timestamp.asc()).all()
    conversation_history = [{"role": "system", "content": "You are a helpful assistant."}] + \
                          [{"role": msg.role, "content": msg.content} for msg in messages]
    user_message = Message(
        chat_id=chat_id_int,
        role="user",
        content=user_input,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(user_message)
    db.session.commit()
    logger.info(f"User message saved for chat_id: {chat_id_int}")
    
    # conversation_history = [{"role": msg.role, "content": msg.content} for msg in messages]
    # conversation_history.append({"role": "user", "content": user_input})

    try:
        full_response = []
        response = get_chatbot_response(user_input, conversation_history, full_response, chat_id_int, db, app)
        logger.info(f"Streaming response started for chat_id: {chat_id_int}")
        return response
    except Exception as e:
        logger.error(f"Error in ask: {str(e)}")
        return jsonify({'error': 'Server error while processing request'}), 500
        # def generate_with_collection():
        #     for chunk in response.stream:
        #         content = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
        #         full_response.append(content)
        #         yield chunk
        # wrapped_response = Response(generate_with_collection(), mimetype='text/plain')
        # @wrapped_response.call_on_close
        # def save_assistant_message():
        #     try:
        #         with app.app_context():  # Use app directly instead of current_app
        #             assistant_content = "".join(full_response)
        #             assistant_message = Message(
        #                 chat_id=chat_id,
        #                 role="assistant",
        #                 content=assistant_content,
        #                 timestamp=datetime.utcnow()
        #             )
        #             db.session.add(assistant_message)
        #             db.session.commit()
        #             logger.info(f"Assistant message saved for chat_id: {chat_id}")
        #     except Exception as e:
        #         logger.error(f"Error saving assistant message: {str(e)}")
        # return wrapped_response
    

        # stream = client.chat.completions.create(
        #     model="deepseek/deepseek-r1:free",
        #     messages=conversation_history,
        #     stream=True
        # )

        # # Store data in g for later use
        # g.chat_id = chat_id
        # g.user_input = user_input

        # def generate():
        #     full_response = []
        #     for chunk in stream:
        #         content = chunk.choices[0].delta.content or ""
        #         full_response.append(content)
        #         yield content.encode('utf-8')
        #     g.full_response = "".join(full_response)
        #     # user_message = Message(
        #     #     chat_id=chat_id,
        #     #     role="user",
        #     #     content=user_input,
        #     #     timestamp = datetime.now(timezone.utc)
        #     # )
        #     # db.session.add(user_message)
        #     # assistant_message = Message(
        #     #     chat_id=chat_id,
        #     #     role="assistant",
        #     #     content="".join(full_response),
        #     #     timestamp = datetime.now(timezone.utc)
        #     # )
        #     # db.session.add(assistant_message)
        #     # db.session.commit()
        # return Response(generate(), mimetype='text/plain')
    # user_input = request.json.get('message')
    # if not user_input:
    #     return jsonify({'error': 'No message provided'}), 400

    # success,message = pdf_Extractor.is_query_relevant(user_input)
    # if not success:
    #     return jsonify({'error':message}),400
    # return get_chatbot_response(user_input)

# @app.teardown_appcontext
# def save_messages(exception):
#     # Check if full_response exists in g (i.e., the generator ran)
#     if hasattr(g, 'full_response'):
#         logger.info(f"Saving messages for chat_id: {g.chat_id}")
#         user_message = Message(
#             chat_id=g.chat_id,
#             role="user",
#             content=g.user_input,
#             timestamp=datetime.utcnow()
#         )
#         db.session.add(user_message)
        
#         assistant_message = Message(
#             chat_id=g.chat_id,
#             role="assistant",
#             content=g.full_response,
#             timestamp=datetime.utcnow()
#         )
#         db.session.add(assistant_message)
#         try:
#             db.session.commit()
#             logger.info("Messages saved successfully")
#         except Exception as e:
#             logger.error(f"Error saving messages: {e}")
#         # db.session.commit()
#     else:
#         logger.warning("No full_response found in g")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    file = request.files['file']
    chat_id = request.form.get('chat_id')
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if str(chat_id).startswith('temp_'):  # Convert chat_id to string
        chat = Chat(name=generate_chat_name())
        db.session.add(chat)
        db.session.commit()
        chat_id = str(chat.id)
    else:
        try:
            chat_id_int = int(chat_id)
        except ValueError:
            return jsonify({'error': 'Invalid chat ID'}), 400
        chat = Chat.query.get_or_404(chat_id_int)
        chat_id = str(chat_id_int)

    temp_path = os.path.join('temp', file.filename)
    os.makedirs('temp', exist_ok=True)
    file.save(temp_path)

    try:
        success, message, raw_text = pdf_Extractor.process_file(temp_path, chat_id, db)
        os.remove(temp_path)
        if success:
            user_message = Message(
                chat_id=int(chat_id),
                role="user",
                content=f"I have uploaded a document named '{file.filename}' with the following content: {raw_text}",
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(user_message)
            assistant_message = Message(
                chat_id=int(chat_id),
                role="assistant",
                content=f"Thank you for uploading the document '{file.filename}'. I have received it and can now answer questions about it.",
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(assistant_message)
            db.session.commit()
            logger.info(f"Document uploaded successfully for chat_id: {chat_id}")
            return jsonify({
                'success': True,
                'chat_id': chat_id,
                'chat_name': chat.name,
                'message': assistant_message.content
            })
        else:
            logger.warning(f"Document upload failed: {message}")
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        os.remove(temp_path) if os.path.exists(temp_path) else None
        return jsonify({'success': False, 'error': f"Server error: {str(e)}"}), 500
    
@app.route('/documents', methods=['GET'])
def get_documents():
    documents = Document.query.all()
    doc_data = []
    for doc in documents:
        chat = Chat.query.get(doc.chat_id)
        doc_data.append({
            'id': doc.id,
            'filename': doc.filename,
            'upload_date': doc.created_at.isoformat(),
            'type': os.path.splitext(doc.filename)[1][1:].upper(),
            'chat_id': doc.chat_id,
            'chat_name': chat.name
        })
    return jsonify(doc_data)

@app.route('/chats/<int:chat_id>/documents/<string:filename>/text', methods=['GET'])
def get_document_text(chat_id, filename):
    messages = Message.query.filter_by(chat_id=chat_id, role='user').all()
    for msg in messages:
        match = re.match(r"I have uploaded a document named '" + re.escape(filename) + r"' with the following content: ([\s\S]*)", msg.content)
        if match:
            return match.group(1)
    return "Document not found", 404

@app.route('/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    doc = Document.query.get_or_404(document_id)
    db.session.delete(doc)
    db.session.commit()
    return '', 204

@app.route('/voice_input', methods=['POST'])
def voice_input():
    data = request.json
    chat_id = data.get('chat_id')
    if not chat_id:
        return jsonify({'error': 'chat_id is required'}), 400
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        return jsonify({'error': 'Invalid chat ID'}), 400
    chat = db.session.get(Chat, chat_id_int)
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404

    # Capture and recognize speech
    user_input = TTS.speech_to_text()
    if user_input is None:
        return jsonify({'error': 'Failed to recognize speech'}), 400

    # Format the recognized text
    formatted_input = TTS.format_sentence(user_input)

    # Save user message to database
    user_message = Message(
        chat_id=chat_id_int,
        role="user",
        content=formatted_input,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(user_message)
    db.session.commit()

    # Get chatbot response
    messages = Message.query.filter_by(chat_id=chat_id_int).order_by(Message.timestamp.asc()).all()
    conversation_history = [{"role": "system", "content": "You are a helpful assistant."}] + \
                          [{"role": msg.role, "content": msg.content} for msg in messages]
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=conversation_history,
            stream=False
        )
        assistant_content = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error getting chatbot response: {str(e)}")
        return jsonify({'error': 'Failed to get chatbot response'}), 500

    # Save assistant message to database
    assistant_message = Message(
        chat_id=chat_id_int,
        role="assistant",
        content=assistant_content,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(assistant_message)
    db.session.commit()

    # Convert response to speech and play it
    TTS.text_to_speech(assistant_content)

    # Return text for client display
    return jsonify({
        'user_input': formatted_input,
        'assistant_response': assistant_content
    })

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    try:
        audio_file = tts_instance.text_to_speech(text)
        audio_url = f"/static/{os.path.basename(audio_file)}"
        return jsonify({'audio_url': audio_url})
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/stt', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_path = 'temp_audio.wav'
    
    try:
        # Save the audio file temporarily
        audio_file.save(audio_path)
        print(f"[INFO] Audio file saved: {audio_path}")

        # Recognize speech using Google Speech Recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            print("[INFO] Reading audio data...")
            audio_data = recognizer.record(source)

        print("[INFO] Recognizing speech...")
        text = recognizer.recognize_google(audio_data)
        print(f"[INFO] Transcription successful: {text}")
        return jsonify({'text': text})

    except sr.UnknownValueError:
        return jsonify({'text': "error: Could not understand audio."})
    except sr.RequestError as e:
        return jsonify({'text': f"error: Google API error: {str(e)}"})
    except Exception as e:
        return jsonify({'text': f"error: {str(e)}"})
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"[INFO] Temporary audio file deleted: {audio_path}")


# @app.route('/stt', methods=['POST'])
# def speech_to_text():
#     if 'audio' not in request.files:
#         return jsonify({'error': 'No audio file provided'}), 400
#     audio_file = request.files['audio']
#     temp_webm = "temp_recording.webm"
#     temp_wav = "temp_audio.wav"
#     try:
#         audio_file.save(temp_webm)
#         # Convert WebM to WAV
#         try:
#             audio = AudioSegment.from_file(temp_webm, format="webm")
#             audio.export(temp_wav, format="wav")
#         except FileNotFoundError as e:
#             logger.error(f"FFmpeg not found: {str(e)}")
#             return jsonify({'error': 'FFmpeg is not installed or not in PATH. Please install FFmpeg.'}), 500
#         text = tts_instance.speech_to_text_from_file(temp_wav)
#         if text is None:
#             return jsonify({'error': 'Could not transcribe audio'}), 400
#         return jsonify({'text': text})
#     except Exception as e:
#         logger.error(f"STT error: {str(e)}")
#         return jsonify({'error': str(e)}), 500
#     finally:
#         # Clean up temporary files
#         for temp_file in [temp_webm, temp_wav]:
#             if os.path.exists(temp_file):
#                 os.remove(temp_file)

if __name__ == '__main__':
    app.run(debug=True)