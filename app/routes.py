from flask import render_template, redirect, url_for
from app import app

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
    return render_template("button.html", title="Button")

@app.route('/share')
def share():
    return render_template("share.html", title="Share")

@app.route('/')
def home():
    #TODO: check if user is logged in, if so redirect to dashboard
    #else redirect to login
    return redirect('/login')

@app.route('/login')
def login_Register():
    return render_template("login.html", title="Login/Register")