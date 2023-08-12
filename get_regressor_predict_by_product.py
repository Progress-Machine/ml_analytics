import json, pickle
import pandas as pd
import numpy as np
from tqdm.notebook import tqdm
from copy import copy, deepcopy
from sklearn.decomposition import PCA
from transformers import AutoImageProcessor, ViTModel
import torch

from clustering import preprocess_data

device = "cpu"

image_processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
model = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")

model.to(device)


pca_vit_transformer = pickle.load(open("models/pca_vit_embeddings.pkl", 'rb'))
regressor = pickle.load(open("models/main_regressor.pkl" ,"rb"))


def get_predict(json_object, image):
    inputs = image_processor(image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    img_embedding = np.array(outputs.pooler_output[0, ...].cpu().detach())
    img_embedding = pca_vit_transformer.transform(img_embedding.reshape(1, -1))

    preprocessed_data = preprocess_data(json_object, normalize_data=False)
    df = preprocessed_data.join(pd.DataFrame(img_embedding, columns=[f"{i + 1}_vit_feature" for i in range(img_embedding.shape[1])]))
    return regressor.predict(df)[0]

