from flask import Flask, render_template, request, redirect, url_for, make_response, flash, session
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess

# instantiate the app
app = Flask(__name__)
app.secret_key = 'weikuo' 

# load credentials and configuration options from .env file
import credentials
config = credentials.get()

# turn on debugging if in development mode
if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mnode

# make one persistent connection to the database
connection = pymongo.MongoClient(config['MONGO_HOST'], 27017, 
                                username=config['MONGO_USER'],
                                password=config['MONGO_PASSWORD'],
                                authSource=config['MONGO_DBNAME'])
db = connection[config['MONGO_DBNAME']] # store a reference to the database

@app.route('/')
def home():
    """
    Route for the home page
    """
    return render_template('index.html')

@app.route('/registration')
def registration():
    """
    Route for the registration page
    """
    return render_template('registration.html')

@app.route('/registration', methods=['POST'])
def registration_post():
    """
    Route for POST requests to the registration page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    name = request.form['fname']
    grade = request.form['fgrade']
    email = request.form['femail']
    password = request.form['fpassword']

    # Check if the email already exists in the database
    email_exists = db.registration.find_one({"email": email}) is not None
    if email_exists:
        # Redirect to the registration page with email_exists as True
        return render_template('registration.html', email_exists=True)
    else:
        # Create a new document with the data the user entered
        doc = {
            "name": name,
            "grade": grade,
            "email": email,
            "password": password,
            "created_at": datetime.datetime.utcnow()
        }
        db.registration.insert_one(doc)

        # After inserting into the database
        flash('Registration successful! Please log in.', 'success')  # 'success' is a category for the message
        return redirect(url_for('login'))
    

@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e) # render the edit template


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/ak8257/error.log',level=logging.DEBUG)
    app.run(debug = True)
