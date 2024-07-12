import argparse
import os
import time

import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse

URL = "https://tululu.org"


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError("Redirect")


def fetch_book_page(url, book_id):
    url_book = f"{url}/b{book_id}/"
    response = requests.get(url_book)
    check_for_redirect(response)

    return BeautifulSoup(response.text, 'lxml')


def get_author_and_title(soup):
    try:
        content_div = soup.find('div', {'id': 'content'}).find('h1')
        text = content_div.text
        text_split = text.split(':')
        title = text_split[0].strip()
        author = text_split[2].strip()
        return title, author
    except AttributeError:
        return None, None


def get_image(soup):
    try:
        content_div = soup.find('div', class_="bookimage").find('a').find("img")
        base_url = "https://tululu.org/"
        relative_url = content_div["src"]
        relative_url_parts = urlparse(relative_url)
        image_url = urljoin(base_url, relative_url_parts.path)
        return image_url
    except AttributeError:
        return None


def get_book_comments(soup):
    comments = soup.find_all(class_="texts")
    for comment in comments:
        return comment.find(class_="black").text


def get_book_genres(soup):
    book_genres = soup.find_all("span", class_="d_book")
    for genre in book_genres:
        for genre_link in genre.find_all("a"):
            return genre_link.text


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


def console_output(title, author, book_comments, book_genre):
    print(f"Название: {title}\nАвтор: {author}")
    print(f"Жанр книги - {book_genre}\n")
    print(f"Комментарий к книге:\n{book_comments}")


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
                title, author = get_author_and_title(soup)
                download_txt(URL, book_id, title, folder='books/')
                image_url = get_image(soup)
                download_image(title, image_url)
                book_comments = get_book_comments(soup)
                book_genre = get_book_genres(soup)
                console_output(title, author, book_comments, book_genre)
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
