import os
import cv2
import numpy as np
import tensorflow as tf
from keras.models import load_model
from keras.preprocessing.image import img_to_array
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session 
import secrets  # Import the secrets module
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
app.config['SECRET_KEY'] = 'e2a14f4eecb16a267e5521a7a56b420adfbdbf6f37282995b988de3c1b310f3a'  # Set your secret key here
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
size = 224


def create_users_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            mobile_number TEXT,
            email TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def email_exists(email):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def process_image(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (size, size))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized_img = clahe.apply(img)
    crop = cv2.resize(equalized_img, (size, size))
    return crop


@app.route('/logout')
def logout():
    # Clear session data
    session.clear()
    # Redirect to the login page
    return render_template('login.html')

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/chart')
def chart():
    return render_template('chart.html')

@app.route('/result')
def result():
    return render_template('result.html')

def validate_credentials(email, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Check if there is a user with the provided email and password
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()

    conn.close()

    # If a user was found, the credentials are valid
    return user is not None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']  # Change 'username' to 'email'
        password = request.form['password']
        
        # Check if username and password are valid
        isValid = validate_credentials(email, password)

        if isValid:
            # Store user information in session (you can customize this as needed)
            session['email'] = email
            return redirect('/upload')
        else:
            return render_template('login.html', error='Invalid email or password')
    else:
        return render_template('login.html')

    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']       
        mobile_number = request.form['mobile-number']
        email = request.form['email']
      
        create_users_table()  # Ensure the users table is created
        
        if email_exists(email):
            return redirect(url_for('signup', email_exists=True))
            # Redirect to signup page with email_exists query parameter

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, mobile_number, email) VALUES (?, ?, ?, ?)', (username, password, mobile_number, email))
        conn.commit()
        conn.close()

        return redirect(url_for('login', signup_success=True))
        # Redirect to login page with signup_success query parameter
    else:
        return render_template('signup.html')
        
# Function to check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    model = load_model('model/modelv7.h5')   
    print("model_loaded")
    target = os.path.join(APP_ROOT, 'static/upload/')
    if not os.path.isdir(target):
        os.mkdir(target)
    filename = ""
    destination = ""
    
    # Check if any file is uploaded
    if 'file' in request.files:
        for file in request.files.getlist("file"):
            filename = file.filename
            destination = os.path.join(target, filename)
            file.save(destination)
        img = cv2.imread(destination)
        cv2.imwrite('static/upload/file.png', img)
        img = process_image(img)
        cv2.imwrite('static/upload/processedfile.png', img)
        img = img.astype('uint8')
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = img_to_array(img)
        img = cv2.resize(img, (size, size))
        img = img.reshape(1, size, size, 3)
        img = img.astype('float32')
        img = img / 255.0
        result = np.argmax(model.predict(img), axis=1)
        pred = model.predict(img)
        neg = pred[0][0]
        pos = pred[0][1]
        classes = ['Negative', 'Positive']
        predicted = classes[result[0]]
        plot_dest = os.path.join(target, "result.png")
        
        labels = ['Negative', 'Positive']
        sizes = [neg, pos]
        colors = ['#ff9999', '#66b3ff']       
        explode = (0, 0.1)  # explode the 2nd slice (i.e., 'Positive')

        plt.figure(figsize=(6, 4))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        # Save the pie chart as an image
        pie_chart_path = os.path.join(target, "pie_chart.png")
        plt.savefig(pie_chart_path)

        # Close the plot to release memory
        plt.close()

        return render_template("result.html", pred=predicted, filename=filename)

    return render_template('upload.html')



if __name__ == '__main__':
    app.run(debug=True)
