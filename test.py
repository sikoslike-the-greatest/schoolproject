from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import json

app = Flask(__name__)

@app.route('/api/products', methods=['GET'])
def get_products():
    # Получаем значения параметров из запроса
    category = request.args.get('category', default=None)
    page = request.args.get('page', default=1, type=int)
    perPage = request.args.get('perPage', default=10, type=int)
    sort = request.args.get('sort', default=None)

    # URL сайта, который ты хочешь спарсить
    url = f'https://poizonshop.ru/{category}?page={page}&perPage={perPage}&sort={sort}'

    # Отправляем GET-запрос к указанному URL
    response = requests.get(url)

    # Проверяем успешность запроса
    if response.status_code == 200:
        # Используем BeautifulSoup для парсинга HTML-кода страницы
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Находим все элементы с классом 'product-card_name__amzGC'
        product_divs = soup.find_all('div', class_='product-card_name__amzGC')
        # Находим все элементы с классом 'product-card-price_product_card_price__ei89N product-card-price_num__5RrTF'
        price_divs = soup.find_all('div', class_='product-card-price_product_card_price__ei89N product-card-price_num__5RrTF')
        # Находим все теги img внутри элементов с классом 'product-card-images_scroll__ekwFS'
        image_tags = soup.select('.product-card-images_scroll__ekwFS img')
        # Находим все теги <a> с классом 'product-card_product_card__5aPyG product-grid-pagination_product__LMyN_'
        link_tags = soup.find_all('a', class_='product-card_product_card__5aPyG product-grid-pagination_product__LMyN_')
        
        # Создаем список для хранения данных о продуктах
        products = []
        
        # Проходим по каждому найденному div и извлекаем текст
        for name_div, price_div, img_tag, link_tag in zip(product_divs, price_divs, image_tags, link_tags):
            product_name = name_div.text.strip()
            
            # Извлекаем число из строки цены, учитывая неразрывные пробелы
            price_text = price_div.text.strip()
            price_value = round(float(re.sub(r'[^\d]+', '', price_text)) * 0.92)  # Округляем до целого числа
            
            product_image_url = img_tag['src']
            product_link = 'https://poizonshopru'+link_tag['href']
            products.append({'name': product_name, 'price': price_value, 'image_url': product_image_url, 'link': product_link})
        
        # Преобразуем список в JSON
        products_json = json.dumps(products, ensure_ascii=False, indent=4)
        
        # Возвращаем JSON-ответ
        return jsonify({'products': products}), 200
    else:
        # Возвращаем сообщение об ошибке
        return jsonify({'error': 'Failed to fetch data'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=56789)
