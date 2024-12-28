from flask import Flask, render_template, request, redirect, url_for, flash, Response
import cv2
import os
import numpy as np
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 1234567890poiuyt" # keep this in .env madhan later

# Global variables
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
webcam = None
uploads_dir = 'uploads'
os.makedirs(uploads_dir, exist_ok=True)
user_faces = {}  # Dictionary to hold registered faces

# Constants for face dimensions
FACE_WIDTH, FACE_HEIGHT = 100, 100

# Load registered faces into memory
def load_registered_faces():
    for filename in os.listdir(uploads_dir):
        if filename.endswith('.jpg'):
            username = filename.rsplit('.', 1)[0]
            filepath = os.path.join(uploads_dir, filename)
            face = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            user_faces[username] = face

# Call to load faces at app startup
load_registered_faces()

# Function to capture a face from the webcam
def capture_face():
    global webcam
    webcam = cv2.VideoCapture(0, cv2.CAP_ANY)  # Use any backend for webcam i am letting opencv to choose the available one

    if not webcam.isOpened():
        print("Error: Could not access the webcam.")
        return None

    ret, frame = webcam.read()
    webcam.release()  # Release the webcam

    if not ret:
        print("Failed to grab frame")
        return None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        print("No face detected")
        return None

    x, y, w, h = faces[0]
    face = gray[y:y + h, x:x + w]  # Extract grayscale / blackand white face region
    return face

# Function to generate video frames for live feed
def gen_frames():
    global webcam
    webcam = cv2.VideoCapture(0, cv2.CAP_ANY)  # Use any backend for webcam

    if not webcam.isOpened():
        print("Error: Could not access the webcam.")
        return

    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            ret, frame = webcam.read()
            if not ret:
                print("Failed to grab frame")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame")
                continue

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    finally:
        webcam.release()  # Ensure the webcam is released

# Route for home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for registering a user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        face = capture_face()

        if face is None:
            flash("Face not detected. Please try again.", 'error')
            return redirect(url_for('register'))

        # Define standard face dimensions
        FACE_WIDTH, FACE_HEIGHT = 100, 100  # Adjust as needed

        # Resize the captured face
        face_resized = cv2.resize(face, (FACE_WIDTH, FACE_HEIGHT))

        # Save the resized face image
        filename = secure_filename(username + '.jpg')
        filepath = os.path.join(uploads_dir, filename)
        cv2.imwrite(filepath, face_resized)

        # Optional: Save the face in memory for immediate use
        user_faces[username] = face_resized

        flash("Registration successful! You can now log in.", 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Route for logging in a user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']

        if username not in user_faces:
            flash("User not registered. Please register first.", 'error')
            return redirect(url_for('register'))

        # Capture a frame from the camera
        video_capture = cv2.VideoCapture(0)
        ret, frame = video_capture.read()
        video_capture.release()

        if not ret or frame is None:
            flash("Failed to capture frame from webcam.", 'error')
            return redirect(url_for('login'))

        # Detect face in the captured frame
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            flash("No face detected. Please try again.", 'error')
            return redirect(url_for('login'))

        # Get the first detected face
        x, y, w, h = faces[0]
        current_face = gray_frame[y:y + h, x:x + w]
        current_face_resized = cv2.resize(current_face, (FACE_WIDTH, FACE_HEIGHT))

        # Compare with the registered face
        saved_face = user_faces[username]

        # Debugging shapes
        print(f"Saved face shape: {saved_face.shape}, Current face shape: {current_face_resized.shape}")

        # Ensure the shapes match
        if saved_face.shape != current_face_resized.shape:
            flash("Shape mismatch between saved and captured face. Try again.", 'error')
            return redirect(url_for('login'))

        diff = cv2.absdiff(saved_face, current_face_resized)
        score = np.sum(diff)

        # Threshold for similarity
        threshold = 10000
        if score < threshold:
            flash(f"Welcome, {username}!", 'success')
            return redirect(url_for('home'))
        else:
            flash("Face does not match. Access denied.", 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


# Route for video feed
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
