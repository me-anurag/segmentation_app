from flask import Flask, render_template, request, jsonify
from segmentation import segment_image

# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        return jsonify({'error': 'Invalid file format'}), 400

    try:
        result = segment_image(file)
        if "error" in result:
            return jsonify({'error': result["error"]}), 500
        return jsonify({
            'segmented_image': result["segmented_image"],
            'analysis': result["analysis"]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)