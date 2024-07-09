import requests
from bs4 import BeautifulSoup



url = 'https://tululu.org/b1/'
response = requests.get(url)
response.raise_for_status()


soup = BeautifulSoup(response.text, 'lxml')

text = soup.find('div', {'id': 'content'}).find('h1').text
text_split = text.split(':')
print(text_split[0])
print(text_split[2].strip())


def download_txt():
    pass
