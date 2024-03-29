from flask import Flask, render_template, request, redirect, url_for, flash, session # make_response
# from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
# import os
# import subprocess

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


@app.route('/login')
def login():
    """
    Route for the login page
    """
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login_post():
    # grade = request.form['fgrade']
    email = request.form['femail']
    password = request.form['fpassword']

    # Check if the user exists in the database
    user = db.registration.find_one({"email": email})

    if user:
        if user['password'] == password:
            # Password matches, login successful
            session['user_email'] = email
            session['user_grade'] = user['grade']
            session['user_fullname'] = user['name']
            flash('Login successful! You can now create and read notes.', 'success')
            return redirect(url_for('home'))
        else:
            # Wrong password
            return render_template('login.html', wrong_password=True)
    else:
        # Email not registered
        return render_template('login.html', email_not_registered=True)

# Logout route
@app.route('/logout')
def logout():
    # Clear the session variables for user logout
    session.pop('user_email', None)
    session.pop('user_grade', None)
    session.pop('user_fullname', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/read/<grade>')
def read(grade):
    """
    Route for GET requests to the read page filtered by grade.
    Displays information for the user with links to other pages based on the chosen grade.
    """
    if grade == 'all':
        docs = db.exampleapp.find().sort("created_at", -1)
    else:
        docs = db.exampleapp.find({"grade": grade}).sort("created_at", -1)
    return render_template('read.html', docs=docs, grade=grade) # render the read template

@app.route('/search_notes', methods=['GET'])
def search_notes():
    search_input = request.args.get('search_input')

    # Perform a query based on the search_input
    # Assuming 'name' is the field in your documents
    docs = db.exampleapp.find({"name": search_input}).sort("created_at", -1)

    return render_template('read.html', docs=docs, grade='all')  # Or pass the correct grade if needed



@app.route('/create')
def create():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    return render_template('create.html') # render the create template


@app.route('/create', methods=['POST'])
def create_post():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    # name = request.form['fname']
    name = session['user_fullname']
    # grade = request.form['fgrade']
    grade = session['user_grade']
    message = request.form['fmessage']


    # create a new document with the data the user entered
    doc = {
        "name": name,
        "message": message, 
        "grade": grade,
        "created_at": datetime.datetime.utcnow()
    }
    db.exampleapp.insert_one(doc) # insert a new document
    # redirect the browser to the read page specific to the grade
    return redirect(url_for('read', grade=grade))

@app.route('/edit/<mongoid>')
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    doc = db.exampleapp.find_one({"_id": ObjectId(mongoid)})
    return render_template('edit.html', mongoid=mongoid, doc=doc) # render the edit template


@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    # name = request.form['fname']
    name = session['user_fullname']
    # grade = request.form['fgrade']
    grade = session['user_grade']
    message = request.form['fmessage']

    doc = {
        # "_id": ObjectId(mongoid), 
        "name": name, 
        "message": message, 
        "grade": grade,
        "created_at": datetime.datetime.utcnow()
    }

    db.exampleapp.update_one(
        {"_id": ObjectId(mongoid)}, # match criteria
        { "$set": doc }
    )

    return redirect(url_for('read', grade=grade)) # tell the browser to make a request for the /read route

@app.route('/delete/<mongoid>')
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    db.exampleapp.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('read', grade='all') ) # tell the web browser to make a request for the /read route.


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
