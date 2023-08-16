from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver

import time
import json
import pickle
import random
from datetime import datetime
from tqdm import tqdm
import requests


headers = {
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
}
home_link = "https://www.wildberries.ru"

useragent = UserAgent()
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={useragent.chrome}")
options.add_argument('--headless')
options.add_argument("--window-size=800,600")

driver = webdriver.Chrome(
    executable_path=r"E:\DIR_python_projects\dnevnikRUselenium\chromedriver.exe",
    options=options)
print(driver.get_window_size())


def get_html(url, params=None):
    global headers
    response = requests.get(url, headers=headers, params=params)

    with open("got.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    return response.text


def get_pages_count(html):
    soup = BeautifulSoup(html, "lxml")

    try:
        good_count = soup.find('span', class_='goods-count').get_text(strip=True).replace("\xa0", '').split()[0]
        good_count = good_count[good_count.index("П")+1:]
        pages_count = int(good_count) // 100 + 1
    except:
        pages_count = 1
    return pages_count


def get_links_cards(base_link, count_scroll=10):
    driver.get(base_link)
    for i in range(count_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links_cards_divs = soup.find_all('a', class_="product-card__link")
    links_cards = list(set([link_card.get('href') for link_card in links_cards_divs]))
    return links_cards




def parse_link(link):
    try:
        driver.get(link)
        time.sleep(2)
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)

        product_soup = BeautifulSoup(driver.page_source, 'html.parser')       #   r.html.html

        try:
            name = product_soup.find("div", class_="product-page__header").find("h1").get_text().strip()
        except:
            name = None

        # цена товара
        try:
            final_price = product_soup.find('ins', class_='price-block__final-price').text.strip().replace("\xa0", '').split()[0][:-1]
        except:
            final_price = None

        try:
            old_price = product_soup.find('del', class_='price-block__old-price').text.strip().replace("\xa0", '').split()[0][:-1]
        except:
            old_price = None

        # кол-во заказов
        try:
            count_orders = product_soup.find("p", class_='product-order-quantity').find("span").text.strip()
            first_flag = count_orders.split()[1]
            second_flag = int("".join([i for i in count_orders.split() if i.isdigit()]))
            if first_flag == "менее":
                count_orders_norm = int(second_flag // 2)
            else:
                count_orders_norm = int(second_flag * 2)
        except Exception:
            count_orders, count_orders_norm = None, None

        # название фирмы-производителя
        name_company = product_soup.find("a", class_="seller-info__name").text.strip()

        # кол-во оценок у продовца
        # try:
        #     celler_count_reviews = product_soup.find("span", class_="seller-info__review").text.strip()
        #     celler_count_reviews = int("".join([i for i in celler_count_reviews.split() if i.isdigit()]))
        # except:
        #     celler_count_reviews = None

        # кол-во товаров, проданных у продавца
        try:
            celler_count_products_sold = product_soup.find("li", class_="seller-info__item seller-info__item--delivered swiper-slide").find("b", class_="seller-info__value").text.strip()
            celler_count_products_sold = int("".join([i for i in celler_count_products_sold.split() if i.isdigit()]))
        except:
            celler_count_products_sold = None

        try:
            celler_percent_bad_products = product_soup.find("li", class_="seller-info__item seller-info__item--defective swiper-slide").find("b", class_="seller-info__value").text.strip()
        except Exception:
            celler_percent_bad_products = None

        try:
            celler_working_time = product_soup.find("li", class_="seller-info__item seller-info__item--time swiper-slide").find("b", class_="seller-info__value").text.strip()
        except Exception:
            celler_working_time = None

        try:
            celler_delivery_mean_time = product_soup.find("li", class_="seller-info__item seller-info__item--delivery swiper-slide").find("b", class_="seller-info__value").text.strip()
        except AttributeError:
            celler_delivery_mean_time = None

        try:
            celler_rating = float(product_soup.find("span", class_="address-rate-mini address-rate-mini--sm").text.strip())
        except Exception:
            celler_rating = None

        try:
            celler_link = product_soup.find("a", class_="seller-info__name seller-info__name--link").get("href")
        except Exception:
            celler_link = None

        try:
            img_link = product_soup.find("div", class_="slide__content img-plug j-wba-card-item").find("img").get("src")
        except:
            img_link = None

        try:
            description = product_soup.find("p", class_="collapsable__text").get_text()
        except Exception:
            description = None

        try:
            comments_link = product_soup.find("a", class_="btn-base comments__btn-all").get("href")
        except:
            comments_link = None

        try:
            tables_params_elements = product_soup.find_all("table", class_="product-params__table")
        except:
            tables_params_elements = None

        text_params = []
        for params in tables_params_elements:
            text_params.append(params.get_text())

        if celler_link is not None:
            celler_link = home_link + celler_link

        if comments_link is not None:
            comments_link = home_link + comments_link

        tmp_dct = \
            {"name": name,
            "url": link,
            "price": final_price,
            "old_price": old_price,
            "order_count": count_orders_norm,
            "celler_sold": celler_count_products_sold,
            "celler_rating": celler_rating,
            "name_comp": name_company,
            "celler_mean_delivery_time": celler_delivery_mean_time,
            "celler_percent_bad_products": celler_percent_bad_products,
            "celler_working_time": celler_working_time,
            "celler_link": celler_link,
            "img_link": img_link,
            "description":description,
            "text_params": text_params,
            "comments_link": comments_link,
            "search_category": None
        }
    except Exception:
        tmp_dct = None

    return tmp_dct