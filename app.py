from flask import Flask, render_template, request, jsonify
import torch
from torchvision import models, transforms
from PIL import Image
import io

# Initialize the Flask app
app = Flask(__name__)

# Load the DeepLabV3 model with the correct weights
from torchvision.models.segmentation import deeplabv3_resnet101
from torchvision.models.segmentation import DeepLabV3_ResNet101_Weights

# Use the correct weights argument to avoid deprecated warnings
model = deeplabv3_resnet101(weights=DeepLabV3_ResNet101_Weights.COCO_WITH_VOC_LABELS_V1)
model.eval()

# Define the image transformation pipeline
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Define routes for Flask
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        # Open the uploaded image
        img = Image.open(file.stream)

        # Apply the necessary transformations
        input_tensor = transform(img).unsqueeze(0)

        # Perform semantic segmentation
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
            output_predictions = output.argmax(0)  # Get the class with the highest score

        # Convert the output predictions into a list
        result = output_predictions.cpu().numpy().tolist()

        return jsonify({'segmentation_result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
