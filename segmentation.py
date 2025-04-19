import torch
from torchvision import models, transforms
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import numpy as np
from scipy.ndimage import label
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        logger.debug("Starting image segmentation")
        # Read file into memory to avoid stream issues
        file_data = file.read()
        logger.debug(f"File data read: {len(file_data)} bytes")

        # Open image from memory
        original_img = Image.open(BytesIO(file_data)).convert("RGB")
        logger.debug(f"Original image opened: {original_img.size}")

        # Resize while preserving aspect ratio
        max_size = 512
        original_img.thumbnail((max_size, max_size), Image.LANCZOS)
        img = Image.new("RGB", (max_size, max_size), (0, 0, 0))
        img.paste(original_img, ((max_size - original_img.width) // 2, (max_size - original_img.height) // 2))
        logger.debug(f"Image resized to: {img.size}")

        # Save original image as base64
        buffered = BytesIO()
        original_img.save(buffered, format="PNG")
        original_img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        logger.debug(f"Original image base64 length: {len(original_img_str)}")

        # Validate base64
        try:
            base64.b64decode(original_img_str)
            logger.debug("Original image base64 validated")
        except Exception as e:
            logger.error(f"Invalid original image base64: {str(e)}")
            return {"error": "Failed to encode original image"}

        # Apply transformations
        input_tensor = transform(img).unsqueeze(0).to(device)
        logger.debug(f"Input tensor shape: {input_tensor.shape}")

        # Perform semantic segmentation
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
            output_predictions = output.argmax(0).cpu().numpy()
        logger.debug(f"Output predictions shape: {output_predictions.shape}")

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
        logger.debug("Segmentation mask created")

        # Calculate object counts and areas, and label each instance
        draw = ImageDraw.Draw(segmented_image)
        try:
            font = ImageFont.truetype("arial.ttf", 14)
            logger.debug("Using arial.ttf font")
        except:
            font = ImageFont.load_default()
            logger.warning("Falling back to default font")

        labeled_instances = []
        for c in range(1, len(CLASSES)):  # Skip background
            mask = (output_predictions == c).astype(np.uint8)
            if np.any(mask):
                labeled_array, num_features = label(mask)
                object_counts[CLASSES[c]] = num_features
                area_percentages[CLASSES[c]] = (np.sum(mask) / total_pixels) * 100

                # Label each instance
                for i in range(1, num_features + 1):
                    instance_mask = (labeled_array == i).astype(np.uint8)
                    coords = np.where(instance_mask)
                    if coords[0].size > 0:
                        centroid = (int(np.mean(coords[1])), int(np.mean(coords[0])))
                        text = CLASSES[c]
                        text_bbox = draw.textbbox(centroid, text, font=font)
                        draw.rectangle(
                            (text_bbox[0] - 5, text_bbox[1] - 5, text_bbox[2] + 5, text_bbox[3] + 5),
                            fill=(0, 0, 0, 128)
                        )
                        draw.text(
                            centroid, text, fill=(255, 255, 255), font=font,
                            stroke_width=1, stroke_fill=(0, 0, 0)
                        )
                        labeled_instances.append((CLASSES[c], centroid))
                logger.debug(f"Labeled {num_features} instances of {CLASSES[c]}")

        # Save segmented image to base64
        buffered = BytesIO()
        segmented_image.save(buffered, format="PNG")
        segmented_img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        logger.debug(f"Segmented image base64 length: {len(segmented_img_str)}")

        # Validate base64
        try:
            base64.b64decode(segmented_img_str)
            logger.debug("Segmented image base64 validated")
        except Exception as e:
            logger.error(f"Invalid segmented image base64: {str(e)}")
            return {"error": "Failed to encode segmented image"}

        # Prepare color mapping
        color_mapping = {cls: f"rgb{COLORS[CLASSES.index(cls)]}" for cls in CLASSES if cls != "background"}

        # Prepare analysis summary
        analysis = {
            "object_counts": {k: int(v) for k, v in object_counts.items() if v > 0 and k != "background"},
            "area_percentages": {k: f"{v:.2f}%" for k, v in area_percentages.items() if v > 0 and k != "background"},
            "color_mapping": color_mapping,
            "total_objects": int(sum(v for k, v in object_counts.items() if k != "background" and v > 0))
        }

        logger.debug(f"Analysis: {analysis}")
        return {
            "segmented_image": segmented_img_str,
            "original_image": original_img_str,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error in segment_image: {str(e)}")
        return {"error": str(e)}
    finally:
        torch.cuda.empty_cache()