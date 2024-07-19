import os

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError("Redirect")


def fetch_book_page(url, book_id):
    url_book = f"{url}/b{book_id}/"
    response = requests.get(url_book)
    check_for_redirect(response)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def get_author_and_title(soup):
    content_div = soup.select_one("#content h1")
    text = content_div.text
    text_split = text.split(':')
    title = text_split[0].strip()
    author = text_split[2].strip()
    return title, author


def get_image(soup, book_id):
    selector = ".bookimage a img"
    content_div = soup.select_one(selector)
    base_url = f"https://tululu.org/b{book_id}/"
    relative_url = content_div["src"]
    relative_url_parts = urlparse(relative_url)
    image_url = urljoin(base_url, relative_url)
    return image_url, relative_url_parts.path


def get_book_comments(soup):
    return soup.select(".texts .black")


def get_book_genres(soup):
    return soup.select("span.d_book a")


def download_txt(url, book_id, filename, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    download_url = f"{url}/txt.php"
    params = {
        "id": book_id,
    }
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f"{filename}.txt")
    response = requests.get(download_url, params=params)
    check_for_redirect(response)
    response.raise_for_status()

    with open(filepath, 'wb') as file:
        file.write(response.content)


def download_image(filename, image_url, folder='images/'):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f"{filename}.jpg")
    response = requests.get(image_url)
    check_for_redirect(response)
    response.raise_for_status()

    with open(filepath, 'wb') as file:
        file.write(response.content)