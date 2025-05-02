# app.py
from flask import Flask, render_template, request, jsonify
from chatbot_convo import get_chatbot_response, conversation_history  
import nltk
from extractor import pdf_Extractor
import os
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('punkt_tab', quiet=True)

app = Flask(__name__)

if not os.path.exists('temp'):
    os.makedirs('temp')

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# # Route for the form page
# @app.route('/form', methods=['GET', 'POST'])
# def form():
#     if request.method == 'POST':
#         name = request.form['name']
#         return render_template('form.html', message=f'Hello, {name}!')
#     return render_template('form.html', message='Please enter your name.')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    success,message = pdf_Extractor.is_query_relevant(user_input)
    if not success:
        return jsonify({'error':message}),400
    return get_chatbot_response(user_input)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Save file temporarily
    temp_path = os.path.join('temp', file.filename)
    file.save(temp_path)
    
    # Process file with extractor
    success, message, raw_text = pdf_Extractor.process_file(temp_path)
    os.remove(temp_path)  # Clean up
    if success:
        # Include file name in conversation history
        conversation_history.append({
            "role": "user",
            "content": f"I have uploaded a document named '{file.filename}' with the following content: {raw_text}"
        })
        conversation_history.append({
            "role": "assistant",
            "content": f"Thank you for uploading the document '{file.filename}'. I have received it and can now answer questions about it."
        })
        return jsonify({
            'success': True,
            'message': f"Thank you for uploading the document '{file.filename}'. I have received it and can now answer questions about it."
        })
    else:
        return jsonify({'success': False, 'error': message}), 400

if __name__ == '__main__':
    app.run(debug=True)


# @app.route('/ask', methods=['POST'])
# def ask():
#     user_input = request.json.get('message')  # Get user input from frontend
#     if not user_input:
#         return jsonify({'error': 'No message provided'}), 400

#     # Get the response from the chatbot logic module
#     assistant_response = get_chatbot_response(user_input)

#     return jsonify({'response': assistant_response})


# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'success': False, 'error': 'No file provided'}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'success': False, 'error': 'No file selected'}), 400
    
#     # Save file temporarily
#     temp_path = os.path.join('temp', file.filename)
#     file.save(temp_path)
    
#     # Process file with extractor
#     success, message, raw_text = pdf_Extractor.process_file(temp_path)
#     os.remove(temp_path)  # Clean up
#     if success:
#         # Generate summary using the LLM
#         summary_prompt = f"Summarize the following document in 100-200 words:\n\n{raw_text}"
#         try:
#             summary_response = client.chat.completions.create(
#                 model="deepseek/deepseek-r1:free",
#                 messages=[{"role": "user", "content": summary_prompt}],
#                 max_tokens=200
#             )
#             summary = summary_response.choices[0].message.content.strip()
#         except Exception as e:
#             summary = "Unable to generate summary due to an error."
#             print(f"Error generating summary: {str(e)}")
        
#         # Include file name and summary in conversation history
#         conversation_history.append({
#             "role": "user",
#             "content": f"I have uploaded a document named '{file.filename}'. Here is a summary: {summary}"
#         })
#         conversation_history.append({
#             "role": "assistant",
#             "content": f"Thank you for uploading the document '{file.filename}'. I have summarized it and can now answer questions based on the summary."
#         })

#         print(conversation_history)
#         return jsonify({
#             'success': True,
#             'message': f"Thank you for uploading the document '{file.filename}'. I have summarized it and can now answer questions based on the summary."
#         })
#     else:
#         return jsonify({'success': False, 'error': message}), 400
