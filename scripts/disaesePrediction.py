import os
import numpy as np
import tensorflow as tf
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from flask_cors import CORS
import gdown
import logging
import h5py
import requests
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Directory to store models in the backend
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Dictionary of model names and their Google Drive direct download links
MODEL_URLS = {
    "Brain_tumor_best_model.h5": "https://drive.google.com/uc?id=1UEr3hcVzzh98yftpKyam57R9dgvvgU3K",
    "chest_xray_model.h5": "https://drive.google.com/uc?id=1SHzJ-7N_R7RsgHNDl0fzsTF1b84b8USN",
    "Vgg16(2).h5": "https://drive.google.com/uc?id=17ipViFN87tRpHbPCMPERwcSdYhVFXFPi"
}

# Minimum expected file size for models (in MB)
MIN_MODEL_SIZE_MB = 10

# Mapping of model types to model files
MODEL_FILES = {
    'eye': 'Vgg16(2).h5',
    'chest': 'chest_xray_model.h5',
    'brain': 'Brain_tumor_best_model.h5'
}

# Validate if a file is a valid HDF5 file
def is_valid_hdf5(file_path):
    try:
        with h5py.File(file_path, 'r') as f:
            return True
    except Exception as e:
        logger.error(f"Invalid HDF5 file {file_path}: {str(e)}")
        return False

# Check if Google Drive link is accessible
def is_url_accessible(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to access URL {url}: {str(e)}")
        return False

# Download a model if it doesn’t exist locally or is invalid
def download_model(model_name):
    model_path = os.path.join(MODEL_DIR, model_name)
    # Check if file exists and is valid; if not, delete and re-download
    if os.path.exists(model_path):
        if not is_valid_hdf5(model_path):
            logger.info(f"Removing invalid file {model_name}")
            os.remove(model_path)
        else:
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
            if file_size < MIN_MODEL_SIZE_MB:
                logger.info(f"Removing small file {model_name} ({file_size:.2f} MB)")
                os.remove(model_path)
    
    if not os.path.exists(model_path):
        url = MODEL_URLS.get(model_name)
        if not url:
            logger.error(f"No URL found for {model_name}")
            raise ValueError(f"No URL found for {model_name}")
        if not is_url_accessible(url):
            logger.error(f"Google Drive URL for {model_name} is not accessible")
            raise ValueError(f"Google Drive URL for {model_name} is not accessible")
        logger.info(f"Downloading {model_name} from {url}...")
        try:
            gdown.download(url, model_path, quiet=False, fuzzy=True)
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
            logger.info(f"Successfully downloaded {model_name} (Size: {file_size:.2f} MB)")
            if file_size < MIN_MODEL_SIZE_MB:
                logger.error(f"Downloaded file {model_name} is too small ({file_size:.2f} MB)")
                os.remove(model_path)
                raise ValueError(f"Downloaded file {model_name} is too small")
            if not is_valid_hdf5(model_path):
                logger.error(f"Downloaded file {model_name} is not a valid HDF5 file")
                os.remove(model_path)
                raise ValueError(f"Downloaded file {model_name} is not a valid HDF5 file")
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {str(e)}")
            raise
    return model_path

labels = {
    'eye': ['Age-Related Macular Degeneration', 'Branch Retinal Vein Occlusion',
            'Diabetic Neuropathy', 'Diabetic Retinopathy', 'Macular Hole', 'Myopia',
            'Optic Disc Cupping', 'Optic Disc Edema', 'Optic Disc Pigmentation',
            'Total Scleral Neurodegeneration'],
    'chest': ['NORMAL', 'PNEUMONIA'],
    'brain': ['glioma_tumor', 'no_tumor', 'meningioma_tumor', 'pituitary_tumor']
}

image_sizes = {
    'eye': (128, 128),
    'chest': (256, 256),
    'brain': (150, 150)
}

@app.route('/', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'OK', 'message': 'HealthSphere Backend is running', 'available_models': list(MODEL_FILES.keys())})

def preprocess_image(image_path, model_type):
    """Loads and preprocesses image for model prediction."""
    try:
        img = load_img(image_path, target_size=image_sizes[model_type])
        img = img_to_array(img)
        img = np.expand_dims(img, axis=0)
        return img
    except Exception as e:
        logger.error("Error preprocessing image for %s: %s", model_type, str(e))
        raise

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files or 'model' not in request.form:
        return jsonify({'error': 'Missing image or model type'}), 400
    
    image_file = request.files['image']
    model_type = request.form['model']

    if model_type not in MODEL_FILES:
        return jsonify({'error': f'Invalid model type. Available models: {list(MODEL_FILES.keys())}'}), 400

    image_path = "temp.jpg"
    try:
        image_file.save(image_path)
        logger.info("Image saved at: %s for %s", image_path, model_type)
    except Exception as e:
        logger.error("Failed to save image: %s", str(e))
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500

    try:
        # Download and load the model on-demand
        model_name = MODEL_FILES[model_type]
        model_path = download_model(model_name)
        logger.info("Loading model %s for %s...", model_name, model_type)
        model = load_model(model_path)

        # Preprocess image and predict
        img = preprocess_image(image_path, model_type)
        prediction = model.predict(img)
        logger.info("Raw prediction for %s: %s", model_type, prediction)

        predicted_index = np.argmax(prediction)
        predicted_label = labels[model_type][predicted_index]

        # Clean up
        os.remove(image_path)
        logger.info("Temporary image removed for %s", model_type)

        # Free up memory
        del model
        gc.collect()
        tf.keras.backend.clear_session()  # Clear TensorFlow session to free memory
        
        return jsonify({'prediction': predicted_label})
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        logger.error("Prediction failed for %s: %s", model_type, str(e))
        return jsonify({'error': f'Prediction failed for {model_type}: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5005))
    app.run(debug=False, host='0.0.0.0', port=port)