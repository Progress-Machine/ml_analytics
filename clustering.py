import json
import pandas as pd
import re
import dateparser
import pickle
import datetime
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation as LDA
import pymorphy2
from sklearn.manifold import TSNE
import umap
from sklearn.neighbors import KDTree
from sklearn.cluster import KMeans
from nltk.corpus import stopwords
from sklearn.preprocessing import StandardScaler, Normalizer

morph = pymorphy2.MorphAnalyzer(lang='ru')
russian_stopwords = stopwords.words("russian")

tfidf = pickle.load(open("models/tdidf.pickle", "rb"))
lda = pickle.load(open("models/lda.pickle", "rb"))
tree = pickle.load(open("models/kd_tree.pickle", "rb"))
normalizer = pickle.load(open("models/normalizer.pickle", "rb"))
umap_clustering = pickle.load(open("models/umap_clustering.pickle", "rb"))

clusters_domain = pd.read_csv("clusters_domain.csv")
origin_df = pd.read_csv("original_data.csv")

column_names_to_normalize = ["price", "old_price", "celler_rating", "celler_mean_delivery_time", "celler_percent_bad_products",
"sale_percent", "percent_order_of_all_seller", "not_info_old_price",
"not_info_order_count", "celler_working_time_norm"]

class TopicModeler(object):
	""" для кластеризации текстов с помощью LDA """
	def __init__(self, tfidf, lda):
		self.lda = lda
		self.tfidf = tfidf

	def __call__(self, text):
		vectorized = self.tfidf.transform([text])
		lda_topics = self.lda.transform(vectorized)
		return lda_topics

	def get_keywords(self, text, n_topics=3, n_keywords=5):
		lda_topics = np.squeeze(self(text), axis=0)
		n_topics_indices = lda_topics.argsort()[-n_topics:][::-1]
		top_topics_words_dists = [self.lda.components_[i] for i in n_topics_indices]
		shape= (n_keywords * n_topics, self.lda.components_.shape[1])
		keywords = np.zeros(shape=shape)
		for i, topic in enumerate(top_topics_words_dists):
			n_keywords_indices = topic.argsort()[-n_keywords:][::-1]
			for k, j in enumerate(n_keywords_indices):
				keywords[i * n_keywords + k, j] = 1
		keywords = [keyword[0] for keyword in self.count_vect.inverse_transform(keywords)]
		return keywords
topic = TopicModeler(tfidf, lda)


def string_to_date(text):
	"""переводим строку с тем сколько работал в число месяцев"""
	if text is None:
		return None
	if text == "Новый магазин":
		return 0
	years, months = 0, 0
	words = text.split()
	if len(words) == 5:
		years = words[0]
		months = words[3]
	elif len(words) == 2:
		if words[1] in ["лет", "года"]:
			years = words[0]
		else:
			months = words[0]
	return int(years) * 12 + int(months)



def preprocess_data(data, normalize_data=True):
	"""
	Функция для предобработки карточки с информацией о товаре для дальнейшей кластеризации и поиска ближайшей продукции.
	Принимает на вход:
		-data: dict, json со всей информацией о карточке человека (как мы парсили с wb)
	Возвращает:
		-df, pd.DataFrame с извлечёнными признаками, который потом юзается для кластеризации и поиска похожих товаров. 
	"""
	df = pd.DataFrame(data).iloc[0]
	df["description"] = re.sub('[0-9:,.!?]', '', df["description"])
	df["description"] = " ".join([morph.parse(word)[0].normal_form for word in df["description"].split() if word not in russian_stopwords])

	if df["price"] is None:
		df["price"] = 0.1
	else:
		df["price"] = float(df["price"])

	if df["old_price"] is None:
		df["old_price"] = 0.1
	else:
		df["old_price"] = float(df["old_price"])

	df["celler_mean_delivery_time"] = float(df["celler_mean_delivery_time"][:df["celler_mean_delivery_time"].index("%")]) if df["celler_mean_delivery_time"] is not None else 99.3
	df["celler_percent_bad_products"] = float(df["celler_percent_bad_products"][:df["celler_percent_bad_products"].index("%")]) if df["celler_percent_bad_products"] is not None else 99.3
	df["sale_percent"] = (df["price"] / df["old_price"]) if df["price"] is not None else 0
	df["not_info_order_count"] = 1 if df["order_count"] is None else 0
	df["celler_sold"] = df["celler_sold"] if df["celler_sold"] is not None else 1
	
	df["percent_order_of_all_seller"] = (df["order_count"] / df["celler_sold"]) if df["order_count"] is not None else 0.03029
	df["not_info_old_price"] = 1 if df["old_price"] is None else 0
	df["celler_working_time_norm"] = string_to_date(df["celler_working_time"])
	
	df.drop(["celler_sold", "comments_link", "celler_working_time", "name",
		 "name_comp", "celler_link", "img_link", "text_params", "search_category"], inplace=True)

	for feature, mean in zip(["celler_working_time_norm", "old_price", "order_count", "price", "celler_rating"],
							 [0.014, 0.58, 0.5, 0.26, 0.002]):
		df[feature] = mean if df[feature] is None else df[feature]
	
	descr = tfidf.transform([df["description"]])
	text_embeddings = lda.transform(descr)
	
	urls = df["url"]
	df.drop(["url", "description"], inplace=True)
	
	columns = ['price', 'old_price', 'order_count', 'celler_rating', 'celler_mean_delivery_time',
			   'celler_percent_bad_products', 'sale_percent', 'percent_order_of_all_seller',
			   'not_info_old_price','not_info_order_count', 'celler_working_time_norm']
	text_embed_df = pd.DataFrame(data=text_embeddings*10, columns=[f"embed_{i}" for i in range(text_embeddings.shape[1])])

	if normalize_data:
		df = pd.DataFrame(data=normalizer.transform(df.values.reshape((1, -1))), columns=columns)
		df = df.join(pd.DataFrame(data=text_embeddings * 10, columns=[f"embed_{i}" for i in range(text_embeddings.shape[1])]))
		return df
	else:
		data = df	# .values.reshape((1, -1))
		return text_embed_df.join(data.to_frame().transpose())



def k_nearest_items(df, k=100, return_idxes=False):
	"""
	Находит самые похожие карточки товара
	Принимает на вход:
		-df, pd.DataFrame с предобработанной информацией о карточке (получается из preprocess_data)
		-k, int кол-во ближайших карточек
		-return_idxes, bool возвращать ли индексы самых похожих товаров
	Возвращает pd.DataFrame с k самыми похожими товарами
	"""
	nearest = tree.query(df.values.reshape(1, -1), k=k)[1][0]
	if return_idxes:
		return nearest

	nearest_samples = origin_df.iloc[nearest]
	return nearest_samples


def position_in_domain(df):
	embedding = umap_clustering.transform(df.values.reshape(1, -1))
	return embedding[0]