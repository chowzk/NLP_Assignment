# app.py
from flask import Flask, render_template, request, jsonify
from chatbot_convo import get_chatbot_response  

app = Flask(__name__)

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
    user_input = request.json.get('message')  # Get user input from frontend
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    # Get the response from the chatbot logic module
    assistant_response = get_chatbot_response(user_input)

    return jsonify({'response': assistant_response})

if __name__ == '__main__':
    app.run(debug=True)