import requests
import json
from typing import List, Dict, Any


def get_products(product_name: str):
    url = "https://real-time-product-search.p.rapidapi.com/search"
    querystring = {
        "q": product_name,
        "country": "us",
        "language": "in",
        "limit": "300"
    }
    headers = {
        "X-RapidAPI-Key": "7a12d3c0a6msh6461c278b79a852p111a13jsnba013a928f97",
        "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)

    with open('realTimeProductSearch.json', 'w') as outfile:
        json.dump(response.json(), outfile)

    if (response.status_code == 200):
        return response.json()['data']
    return []


def priceParser(price: str) -> float:
    return float('.'.join(price[3:].split(',')))


def get_cheapest_product(products: List[Dict[str, Any]]):
    cheapest_product = products[0]
    for product in products:
        try:
            # print(priceParser(product['offer']['price']))
            # print(product['product_rating'])
            if (priceParser(product['offer']['price']) < priceParser(
                    cheapest_product['offer']['price'])):
                cheapest_product = product
        except:
            pass
    return cheapest_product


def filter_by_ratings(required_rating: float, products: List[Dict[str, Any]]):
    return [
        product for product in products
        if float(0 if product['product_rating'] ==
                 None else product['product_rating']) >= required_rating
    ]