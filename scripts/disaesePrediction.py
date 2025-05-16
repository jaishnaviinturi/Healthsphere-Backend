import os
import numpy as np
import tensorflow as tf
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model # type: ignore
from tensorflow.keras.preprocessing.image import load_img, img_to_array # type: ignore
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

try:
    models = {
        'eye': load_model(r'E:\VScode\HealthSphere\frontend\scripts\models\Vgg16 (2).h5'),
        'chest': load_model(r'E:\VScode\HealthSphere\frontend\scripts\models\chest_xray_model.h5'),
        'brain': load_model(r'E:\VScode\HealthSphere\frontend\scripts\models\Brain_tumor_best_model.h5')
    }
    print("All models loaded successfully:", list(models.keys()))
except Exception as e:
    print(f"Error loading models: {e}")
    raise

labels = {
    'eye': ['Age-Related Macular Degeneration', 'Branch Retinal Vein Occlusion',
            'Diabetic Neuropathy', 'Diabetic Retinopathy', 'Macular Hole', 'Myopia',
            'Optic Disc Cupping', 'Optic Disc Edema', 'Optic Disc Pigmentation',
            'Total Scleral Neurodegeneration'],
    'chest': ['NORMAL', 'PNEUMONIA'],
    'brain': ['glioma_tumor', 'no_tumor','meningioma_tumor' , 'pituitary_tumor']
}

image_sizes = {
    'eye': (128, 128),
    'chest': (256, 256),
    'brain': (150, 150)
}

def preprocess_image(image_path, model_type):
    """Loads and preprocesses image for model prediction."""
    try:
        img = load_img(image_path, target_size=image_sizes[model_type])
        img = img_to_array(img)
        
        img = np.expand_dims(img, axis=0)
        return img
    except Exception as e:
        print(f"Error preprocessing image for {model_type}: {e}")
        raise

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files or 'model' not in request.form:
        return jsonify({'error': 'Missing image or model type'}), 400
    
    image_file = request.files['image']
    model_type = request.form['model']

    if model_type not in models:
        return jsonify({'error': 'Invalid model type. Use "eye", "chest", or "brain"'}), 400

    image_path = "temp.jpg"
    try:
        image_file.save(image_path)
        print(f"Image saved at: {image_path} for {model_type}")
    except Exception as e:
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500

    try:
        img = preprocess_image(image_path, model_type)
        prediction = models[model_type].predict(img)
        print(f"Raw prediction for {model_type}: {prediction}")

        predicted_index = np.argmax(prediction)
        predicted_label = labels[model_type][predicted_index]

        os.remove(image_path)
        print(f"Temporary image removed for {model_type}")
        
        return jsonify({'prediction': predicted_label})
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({'error': f'Prediction failed for {model_type}: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)