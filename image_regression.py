import torch
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--model_path', type=str, default='C:/Deep Learning/ml_analytics/data/model_image_regressor.pt')
parser.add_argument('--extractor_path', type=str, default='C:/Deep Learning/ml_analytics/data/extractor.pt')
parser.add_argument('--image_path', type=str, default='C:/Deep Learning/ml_analytics/data/4.jpg')
parser.add_argument('--device', type=str, default='cuda')
args = parser.parse_args()

device = args.device
model = torch.load(args.model_path)
model.to(device).eval()
extractor = torch.load(args.extractor_path)

image = Image.open(args.image_path)
inputs = extractor(images=image, return_tensors="pt").pixel_values.to(device)
with torch.no_grad():
    pred = model(inputs).logits.item()
pred = round(pred, 2)
print(pred)    # max 200000