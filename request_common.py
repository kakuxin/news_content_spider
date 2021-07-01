import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
}


def get_soup(url, encoding='utf-8'):
    response = requests.get(url, headers=headers)
    response.encoding = encoding
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def get_json(url):
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    data = json.loads(response.text)
    return data