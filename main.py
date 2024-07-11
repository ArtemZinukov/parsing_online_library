import argparse
import os
import time

import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin

URL = "https://tululu.org"


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError("Redirect")
    return response


def fetch_book_page(url, book_id):
    url_book = f"{url}/b{book_id}/"
    response = requests.get(url_book)
    response.raise_for_status()

    return BeautifulSoup(response.text, 'lxml')


def get_author_and_title(soup):
    content_div = soup.find('div', {'id': 'content'})
    if content_div:
        h1_tag = content_div.find('h1')
        if h1_tag:
            text = h1_tag.text
            text_split = text.split(':')
            title = text_split[0].strip()
            author = text_split[2].strip()
            print(f"Название: {title}\nАвтор: {author}")
            return title, author
    return None, None


def get_image(soup):
    content_div = soup.find('div', class_="bookimage")
    if content_div:
        image_tag = content_div.find('a').find("img")
        if image_tag:
            image_url = urljoin("https://tululu.org/", image_tag["src"])
            return image_url
    return None


def get_book_comments(soup):
    comments = soup.find_all(class_="texts")
    for comment in comments:
        print(f"Комментарий к книге:\n{comment.find(class_="black").text}")


def get_book_genre(soup):
    book_genres = soup.find_all("span", class_="d_book")
    for genre in book_genres:
        for genre_link in genre.find_all("a"):
            print(f"Жанр книги - {genre_link.text}\n")


def download_txt(url, book_id, filename, folder='books/'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    download_url = f"{url}/txt.php"
    params = {
        "id": book_id,
    }
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f"{filename}.txt")
    response = requests.get(download_url, params=params)
    response = check_for_redirect(response)
    print(response.url)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def download_image(filename, soup, folder='images/'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f"{filename}.jpg")
    image_url = get_image(soup)
    response = requests.get(image_url)
    response = check_for_redirect(response)

    with open(filepath, 'wb') as file:
        file.write(response.content)


def main():
    Path("./books").mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(prog='main', description='запускает скрипт для скачивания книг')
    parser.add_argument('start_id', default=1, help="Укажите начальный ID книги для скачивания",
                        type=int)
    parser.add_argument('end_id', default=11, help="Укажите конечный ID книги для скачивания",
                        type=int)
    parser_args = parser.parse_args()
    for book_id in range(parser_args.start_id, parser_args.end_id+1):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                soup = fetch_book_page(URL, book_id)
                filename, author = get_author_and_title(soup)
                download_txt(URL, book_id, filename, folder='books/')
                download_image(filename, soup)
                get_book_comments(soup)
                get_book_genre(soup)
                break
            except requests.ConnectionError as err:
                print(f"Ошибка соединения для книги - {book_id} (попытка {attempt+1}/{max_attempts}): {err}")
                if attempt < max_attempts - 1:
                    time.sleep(10)
                    continue
                else:
                    raise
            except requests.RequestException as err:
                print(f"Ошибка загрузки книги - {book_id}: {err}")


if __name__ == "__main__":
    main()
