import numpy as np
from wordcloud import WordCloud
from nltk.corpus import stopwords

stop_words = stopwords.words('russian')

from clustering import k_nearest_items, clusters_domain, preprocess_data

def get_analytics(out_product, create_worldcloud=True):
    """Делает аналитику - возвращает словари с результатами, сохраняет облако слов в tmp_files/world-cloud.png
    если флаг create_worldcloud=True
    out_product: dict с информацией о карточке товара, полученный после парсинга
    """
    processed_data = preprocess_data(out_product)
    nearest_dataframe = k_nearest_items(processed_data)

    if create_worldcloud: _create_worldcloud(nearest_dataframe)

    results = {
        "revenue_analytic": _get_revenue_analytic(nearest_dataframe, out_product),
        "price_analytic": _get_price_analytic(nearest_dataframe, out_product),
        "rating_analytic": _get_rating_analytic(nearest_dataframe, out_product)
    }

    return results



def _get_revenue_analytic(nearest_dataframe, out_product):
    """производит аналитику по выручке - локальная функция, только для использования в файле"""
    nearest_dataframe["revenue"] = nearest_dataframe.order_count * nearest_dataframe.price

    our_revenue = out_product["price"] * out_product["order_count"] if out_product["order_count"] is not None else 0
    # revenue_median = nearest_dataframe.revenue.median()

    percentile = sum(our_revenue < nearest_dataframe.revenue) / len(nearest_dataframe.revenue) * 100

    comment = f"Ваша выручка по продукту выше чем у {percentile} похожих товаров. "
    if percentile < 80:
        comment += "Мы поможем улучшить это число!"
    else:
        comment += "Поздравляем! Это крутой результат!"

    dct_revenue = {"nearest_revenues": list(nearest_dataframe.revenue),
                   "our_revenue": our_revenue,
                   "comment": comment
                   }

    return dct_revenue


def _get_price_analytic(nearest_dataframe, out_product):
    """производит аналитику по цене товара - локальная функция, только для использования в файле"""

    best_price = nearest_dataframe.sort_values(by="revenue", ascending=False).iloc[:25].price.mean()
    mean_price = nearest_dataframe.price.mean()
    our_price = float(out_product["price"])

    comment = f"Выша цена: {our_price}. Средняя цена в среди похожих товаров: {mean_price}; " \
              f"Цена у товаров с наибольшей выручкой: {best_price}"

    comment2 = ""
    if our_price < best_price * 0.9:
        comment2 = "Возможно, Вам стоит повысить цену или снизить издержки на доставку. Мы поможем Вам реализовать потенциал продукта с помощью AI технологий"
    elif our_price > best_price * 1.1:
        comment2 += "Возможно, Вам стоит понизить цену или усилить маркетинговую часть, чтобы донести клиентам ценность продукта. Мы поможем Вам это сделать с помощью AI технологий"

    dct_price = {"comment": comment, "personal_comment": comment2,
                 "nearest_prices": list(nearest_dataframe.price), "our_price": out_product["price"]}

    return dct_price


def _get_rating_analytic(nearest_dataframe, out_product):
    """производит аналитику по рейтингу товара - локальная функция, только для использования в файле"""

    our_rating = out_product["celler_rating"]
    percentile = sum(our_rating < nearest_dataframe.celler_rating) / len(nearest_dataframe.celler_rating) * 100

    comment = ""
    if percentile < 30:
        comment = f"Ваш рейтинг по карточке ниже чем у {100 - percentile} похожих товаров. Это может отталкивать потенциальных покупателей при выборе товара. Для увеличения рейтинга и повышения доверия к бренду можно воспользоваться нашим генератором положительных отзывов на товар"
    elif percentile > 60:
        comment = f"Ваш рейтинг по карточке выше чем у {percentile} похожих товаров. Это высокий показатель, чтобы преобразовать его в высокую выручку рассмотрите возможность запустить рекламу на маркетплейсе и других популярных платформах"
    else:
        comment = f"Ваш рейтинг по карточке близок к среднему, но для повышения рейтинга и попадания в выдачу можно воспользоваться нашим генератором положительных отзывов на товар"

    dct_rating = {"comment": comment, "nearest_ratings": list(nearest_dataframe.celler_rating),
                  "our_rating": our_rating}
    return dct_rating


def _create_worldcloud(nearest_dataframe):
    """создает облака слов из слов описаний карточек товаров"""
    text = " ".join([i for i in nearest_dataframe.description if i is not np.nan])
    cloud = WordCloud(width=1920, height=1080, stopwords=stop_words,
                      background_color="rgba(255, 255, 255, 0)").generate(text)
    cloud.to_file("tmp_files/world_cloud.png")
