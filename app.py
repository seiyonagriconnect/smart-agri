from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import pickle
import numpy as np
import pandas as pd
import cv2
import json
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

app = Flask(__name__)

# Load models
crop_model = pickle.load(open('models/Crop_Recommendation.pkl', 'rb'))
pest_model = load_model("models/pest_model.keras", compile=False)

# Load fertilizer dictionary
from utils.fertilizer import fertilizer_dic

# Load pesticide data
with open("Data/pesticides.json", "r", encoding="utf-8") as f:
    pesticide_info = json.load(f)

# Load OpenCV human detection model
net = cv2.dnn.readNetFromCaffe("models/deploy.prototxt", "models/mobilenet_iter_73000.caffemodel")

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_human(img_path):
    image_data = cv2.imread(img_path)
    blob = cv2.dnn.blobFromImage(cv2.resize(image_data, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            class_id = int(detections[0, 0, i, 1])
            if class_id == 15:
                return True
    return False

def predict_pest(img_path):
    if detect_human(img_path):
        return "Human Detected", {"error": "Please upload a pest image, not a human image."}

    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    prediction = pest_model.predict(img_array)
    class_labels = list(pesticide_info.keys())

    if len(prediction[0]) != len(class_labels):
        return "Unknown Pest", {}

    detected_pest = class_labels[np.argmax(prediction[0])]
    return detected_pest, pesticide_info.get(detected_pest, {})

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template("login-signup.html")

@app.route('/subscription-plans')
def subscription_plans():
    return render_template('subscription-plans.html')

@app.route('/pickup-points')
def pickup_points():
    return render_template('pickup-points.html')

@app.route('/pre-launch-offer')
def pre_launch_offer():
    return render_template('pre-launch-offer.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/for-farmers')
def for_farmers():
    return render_template('for-farmers.html')


@app.route('/smart-agri')
def main_index():
    return render_template('smart_agri.html')


@app.route("/crop-recommend")
def crop_recommend():
    return render_template("crop.html")

@app.route('/crop-predict', methods=['POST'])
def crop_prediction():
    try:
        N = int(request.form['nitrogen'])
        P = int(request.form['phosphorous'])
        K = int(request.form['pottasium'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])

        data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        prediction = crop_model.predict(data)[0]
        return render_template('crop-result.html', prediction=prediction)
    except Exception as e:
        return f"Error: {e}"

@app.route("/fertilizer")
def fertilizer_recommendation():
    return render_template("fertilizer.html")

@app.route('/fertilizer-predict', methods=['POST'])
def fert_recommend():
    crop_name = str(request.form['cropname'])
    N = int(request.form['nitrogen'])
    P = int(request.form['phosphorous'])
    K = int(request.form['pottasium'])

    df = pd.read_csv('Data/fertilizer.csv')
    nr = df[df['Crop'] == crop_name]['N'].iloc[0]
    pr = df[df['Crop'] == crop_name]['P'].iloc[0]
    kr = df[df['Crop'] == crop_name]['K'].iloc[0]

    n = nr - N
    p = pr - P
    k = kr - K
    max_diff = max((abs(n), 'N'), (abs(p), 'P'), (abs(k), 'K'))[1]

    key = f"{max_diff}{'High' if locals()[max_diff.lower()] < 0 else 'low'}"
    recommendation = fertilizer_dic[key]

    return render_template('fertilizer-result.html', recommendation=recommendation)

@app.route("/pesticide_recommendation")
def pesticide_recommendation():
    return render_template("pesticide_recommendation.html")

@app.route("/pesticide_result", methods=["POST"])
def pesticide_result():
    if "file" not in request.files:
        return redirect(url_for("pesticide_recommendation"))

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return redirect(url_for("pesticide_recommendation"))

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    pest_name, pest_data = predict_pest(filepath)

    return render_template("pesticide_result.html", pest=pest_name, pest_data=pest_data, image_path=filepath)



if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
