from flask import Flask, render_template, request, jsonify
from segmentation import segment_image  # Import the function

# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')  # Renders your homepage

@app.route('/index')
def index():
    return render_template('index.html')  # Renders segmentation page

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        segmented_image = segment_image(file)
        return jsonify({'segmented_image': segmented_image})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
