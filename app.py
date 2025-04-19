from flask import Flask, render_template, request, jsonify
from segmentation import segment_image
import logging

# Initialize the Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    logger.debug("Received predict request")
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        logger.error(f"Invalid file format: {file.filename}")
        return jsonify({'error': 'Invalid file format'}), 400

    try:
        result = segment_image(file)
        if "error" in result:
            logger.error(f"Segmentation error: {result['error']}")
            return jsonify({'error': result["error"]}), 500
        logger.debug(f"Segmentation response: {list(result.keys())}")
        return jsonify({
            'segmented_image': result["segmented_image"],
            'original_image': result.get("original_image", ""),
            'analysis': result["analysis"]
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)