from flask import render_template
from app import app
@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    posts = [
    {
    'author': {'username': 'John'},
    'body': 'Beautiful day in Portland!'
    },
    {
    'author': {'username': 'Susan'},
    'body': 'The Avengers movie was so cool!'
    }
    ]
    return render_template("index.html", title="Home", user=user, posts=posts)

@app.route('/button')
def button():
    return render_template("button.html", title="Button!")

@app.route('/share')
def share():
    return render_template("share.html", title="Share")