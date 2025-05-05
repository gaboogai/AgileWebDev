
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  

@app.route('/upload', methods=['POST'])
def upload():
    title = request.form.get('title')
    artist = request.form.get('artist')
    
    print(f"Song title: {title}, Artist name: {artist}")

    return redirect(url_for('index'))  

if __name__ == '__main__':
    app.run(debug=True)
