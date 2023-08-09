import torch
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--model_path', type=str, default='C:/Deep Learning/ml_analytics/data/model_text_regressor.pt')
parser.add_argument('--tokenizer_path', type=str, default='C:/Deep Learning/ml_analytics/data/roberta_tokenizer.pt')
parser.add_argument('--json_path', type=str, default='C:/Deep Learning/ml_analytics/resule_parsing.json')
parser.add_argument('--device', type=str, default='cuda')
args = parser.parse_args()

device = args.device
model = torch.load(args.model_path)
model.to(device).eval()
tokenizer = torch.load(args.tokenizer_path)

with open(args.json_path, encoding='utf-8') as f:
    text = json.load(f)[0]['description']

output = tokenizer(text, max_length=128,  pad_to_max_length=True, return_tensors='pt')
ids = output['input_ids'].to(device)
masks = output['attention_mask'].to(device)
with torch.no_grad():
    pred = model(ids, masks).logits.flatten().item()
pred = round(pred, 2)
print(pred)

