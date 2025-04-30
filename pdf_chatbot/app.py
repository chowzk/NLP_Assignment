# app.py
from flask import Flask, render_template, request

app = Flask(__name__)

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for the form page
@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form['name']
        return render_template('form.html', message=f'Hello, {name}!')
    return render_template('form.html', message='Please enter your name.')

if __name__ == '__main__':
    app.run(debug=True)