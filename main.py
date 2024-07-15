import argparse
import os
import time
import json

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
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def fetch_books_by_genre(page):
    url_book = f"https://tululu.org/l55/{page}/"
    response = requests.get(url_book)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def get_author_and_title(soup):
    content_div = soup.find('div', {'id': 'content'}).find('h1')
    text = content_div.text
    text_split = text.split(':')
    title = text_split[0].strip()
    author = text_split[2].strip()
    return title, author


def get_image(soup, book_id):
    content_div = soup.find('div', class_="bookimage").find('a').find("img")
    base_url = f"https://tululu.org/b{book_id}/"
    relative_url = content_div["src"]
    relative_url_parts = urlparse(relative_url)
    image_url = urljoin(base_url, relative_url_parts.path)
    return image_url, relative_url_parts.path


def get_book_comments(soup):
    return soup.find_all(class_="texts")


def get_book_genres(soup):
    return soup.find("span", class_="d_book").find_all("a")


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


def download_book_from_page(soup):
    content_div = soup.find_all('div', class_="bookimage")
    book_ids = []
    for book_div in content_div:
        content = book_div.find("a")

        relative_url = content["href"]
        relative_url_parts = urlparse(relative_url)
        book_ids.append(relative_url_parts.path.split("/b")[1])
    return book_ids


def download_all_book(book_ids):
    for book_id in book_ids:
        try:
            soup = fetch_book_page(URL, book_id)
            title, author = get_author_and_title(soup)
            download_txt(URL, book_id, title, folder='books/')
            image_url, relative_url = get_image(soup, book_id)
            download_image(title, image_url)
            book_comments = get_book_comments(soup)
            book_genres = get_book_genres(soup)
            console_output(title, author, book_comments, book_genres)
            create_json_output(title, author, relative_url, book_comments, book_genres)
        except (AttributeError, requests.RequestException) as err:
            print(f"Ошибка загрузки книги - {book_id}: {err}")


def console_output(title, author, book_comments, book_genres):
    print(f"Название: {title}\nАвтор: {author}")
    print("\nЖанр книги: ")
    for genre_link in book_genres:
        print(f"{genre_link.text}")
    print(f"\nКомментарии к книге: ")
    for comment in book_comments:
        print(f"{comment.find(class_="black").text}")


def create_json_output(title, author, image_url, book_comments, book_genres):
    books_info = {
        "title": title,
        "author": author,
        "img_src": image_url,
        "comments": [str(f"{comment.find(class_="black").text}") for comment in book_comments],
        "genres": [str(f"{genre.text}") for genre in book_genres]
    }
    books_info_json = json.dumps(books_info, ensure_ascii=False, indent=4)

    with open("books_info.json", "a", encoding='utf8') as my_file:
        my_file.write(books_info_json)


def main():
    Path("./books").mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(prog='main', description='запускает скрипт для скачивания книг')
    parser.add_argument('--start_id', default=1, help="Укажите начальный ID книги для скачивания",
                        type=int)
    parser.add_argument('--end_id', default=11, help="Укажите конечный ID книги для скачивания",
                        type=int)
    parser.add_argument('--start_page', help="Укажите начальную страницу с книгами для скачивания",
                        type=int)
    parser.add_argument('--end_page', help="Укажите конечную страницу с книгами для скачивания",
                        type=int)
    parser_args = parser.parse_args()
    for book_id in range(parser_args.start_id, parser_args.end_id+1):
        attempt = 0
        while True:
            try:
                soup = fetch_book_page(URL, book_id)
                title, author = get_author_and_title(soup)
                download_txt(URL, book_id, title, folder='books/')
                image_url = get_image(soup, book_id)
                download_image(title, image_url)
                book_comments = get_book_comments(soup)
                book_genres = get_book_genres(soup)
                console_output(title, author, book_comments, book_genres)
                break
            except requests.ConnectionError as err:
                print(f"Ошибка соединения для книги - {book_id} (попытка {attempt+1}): {err}")
                time.sleep(10)
                attempt += 1
            except (AttributeError, requests.RequestException) as err:
                print(f"Ошибка загрузки книги - {book_id}: {err}")
                break
    for book_page in range(parser_args.start_page, parser_args.end_page):
        attempt = 0
        while True:
            try:
                soup = fetch_books_by_genre(book_page)
                book_ids = download_book_from_page(soup)
                download_all_book(book_ids)
                break
            except requests.ConnectionError as err:
                print(f"Ошибка соединения для книги - {book_page} (попытка {attempt + 1}): {err}")
                time.sleep(10)
                attempt += 1


if __name__ == "__main__":
    main()
