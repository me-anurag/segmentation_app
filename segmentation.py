# segmentation.py
import torch
from torchvision import models, transforms
from PIL import Image
from io import BytesIO
import base64
import numpy as np

# Load the DeepLabV3 model with the correct weights
from torchvision.models.segmentation import deeplabv3_resnet101
from torchvision.models.segmentation import DeepLabV3_ResNet101_Weights

# Initialize the model
model = deeplabv3_resnet101(weights=DeepLabV3_ResNet101_Weights.COCO_WITH_VOC_LABELS_V1)
model.eval()

# Define the image transformation pipeline
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Color map for segmentation classes (20 categories for VOC dataset)
COLORS = [
    (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128), (128, 0, 128),
    (0, 128, 128), (128, 128, 128), (64, 0, 0), (192, 0, 0), (64, 128, 0), (192, 128, 0),
    (64, 0, 128), (192, 0, 128), (64, 128, 128), (192, 128, 128), (0, 64, 0), (128, 64, 0),
    (0, 192, 0), (128, 192, 0)
]

def segment_image(file):
    try:
        # Open the uploaded image
        img = Image.open(file.stream)

        # Apply the necessary transformations
        input_tensor = transform(img).unsqueeze(0)

        # Perform semantic segmentation
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
            output_predictions = output.argmax(0)  # Get the class with the highest score

        # Map the predictions to colors
        segmentation_result = np.zeros((output_predictions.shape[0], output_predictions.shape[1], 3), dtype=np.uint8)
        for c in range(len(COLORS)):
            segmentation_result[output_predictions == c] = COLORS[c]

        # Convert to a PIL image for visualization
        segmented_image = Image.fromarray(segmentation_result)

        # Save the segmented image to an in-memory file and encode it to base64
        buffered = BytesIO()
        segmented_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return img_str

    except Exception as e:
        return str(e)
