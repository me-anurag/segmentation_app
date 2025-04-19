import torch
from torchvision import models, transforms
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import numpy as np
from scipy.ndimage import label  # Explicit import

# Debugging import
try:
    print("Successfully imported scipy.ndimage.label")
except ImportError as e:
    print(f"Failed to import scipy.ndimage.label: {e}")

# Load the DeepLabV3 model
from torchvision.models.segmentation import deeplabv3_resnet101
from torchvision.models.segmentation import DeepLabV3_ResNet101_Weights

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = deeplabv3_resnet101(weights=DeepLabV3_ResNet101_Weights.COCO_WITH_VOC_LABELS_V1).to(device)
model.eval()

# Image transformation pipeline
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# VOC classes and colors
CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair",
    "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa",
    "train", "tvmonitor"
]
COLORS = [
    (0, 0, 0), (255, 102, 102), (102, 255, 102), (102, 102, 255), (255, 255, 102),
    (255, 102, 255), (102, 255, 255), (255, 178, 102), (178, 102, 255), (102, 178, 255),
    (255, 102, 178), (178, 255, 102), (102, 255, 178), (255, 178, 178), (178, 178, 255),
    (255, 255, 178), (178, 255, 255), (255, 178, 255), (178, 102, 178), (102, 178, 178),
    (178, 178, 178)
]

def segment_image(file):
    try:
        # Open and resize the uploaded image
        img = Image.open(file.stream).convert("RGB")
        img = img.resize((512, 512), Image.LANCZOS)
        print(f"Image resized to: {img.size}")

        # Apply transformations
        input_tensor = transform(img).unsqueeze(0).to(device)
        print(f"Input tensor shape: {input_tensor.shape}")

        # Perform semantic segmentation
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
            output_predictions = output.argmax(0).cpu().numpy()
        print(f"Output predictions shape: {output_predictions.shape}")

        # Initialize data for analysis
        object_counts = {cls: 0 for cls in CLASSES}
        area_percentages = {cls: 0.0 for cls in CLASSES}
        total_pixels = output_predictions.size

        # Create segmentation mask
        segmentation_result = np.zeros((output_predictions.shape[0], output_predictions.shape[1], 3), dtype=np.uint8)
        for c in range(len(COLORS)):
            segmentation_result[output_predictions == c] = COLORS[c]

        # Convert to PIL image
        segmented_image = Image.fromarray(segmentation_result)

        # Calculate object counts and areas using connected components per class
        print("Attempting to label objects...")
        for c in range(1, len(CLASSES)):  # Start from 1 to skip background
            mask = (output_predictions == c).astype(np.uint8)
            if np.any(mask):
                labeled_array, num_features = label(mask)
                object_counts[CLASSES[c]] = num_features
                area_percentages[CLASSES[c]] = (np.sum(mask) / total_pixels) * 100

        # Find centroids for labeling
        centroids = {}
        for cls in CLASSES[1:]:  # Skip background
            mask = (output_predictions == CLASSES.index(cls)).astype(np.uint8)
            if np.any(mask):
                coords = np.where(mask)
                if coords[0].size > 0:
                    centroid = (int(np.mean(coords[1])), int(np.mean(coords[0])))
                    centroids[cls] = centroid

        # Draw labels on segmented image
        draw = ImageDraw.Draw(segmented_image)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        for cls, centroid in centroids.items():
            draw.text(centroid, cls, fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))

        # Save segmented image to base64
        buffered = BytesIO()
        segmented_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Prepare color mapping
        color_mapping = {cls: f"rgb{COLORS[CLASSES.index(cls)]}" for cls in CLASSES if cls != "background"}

        # Prepare analysis summary
        analysis = {
            "object_counts": {k: int(v) for k, v in object_counts.items() if v > 0 and k != "background"},  # Ensure int
            "area_percentages": {k: f"{v:.2f}%" for k, v in area_percentages.items() if v > 0 and k != "background"},
            "color_mapping": color_mapping,
            "total_objects": int(sum(v for k, v in object_counts.items() if k != "background" and v > 0))  # Ensure int
        }

        print(f"Analysis: {analysis}")
        return {"segmented_image": img_str, "analysis": analysis}

    except Exception as e:
        print(f"Error in segment_image: {e}")
        return {"error": str(e)}
    finally:
        torch.cuda.empty_cache()  # Clear GPU memory