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


def fetch_catalog_page(page_number):
    url_catalog_page = f"https://tululu.org/l55/{page_number}/"
    response = requests.get(url_catalog_page)
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
    image_url = urljoin(base_url, relative_url_parts.path)
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


def extract_book_ids(soup):
    content_div = soup.select(".bookimage a")
    book_ids = []
    for content in content_div:
        relative_url = content["href"]
        relative_url_parts = urlparse(relative_url)
        book_ids.append(relative_url_parts.path.split("/b")[1])
    return book_ids


def download_all_book(book_ids, dest_folder, skip_txt=False, skip_imgs=False):
    for book_id in book_ids:
        try:
            soup = fetch_book_page(URL, book_id)
            title, author = get_author_and_title(soup)
            if not skip_txt:
                download_txt(URL, book_id, title, folder=dest_folder)
            if not skip_imgs:
                image_url, relative_url = get_image(soup, book_id)
                download_image(title, image_url, folder=dest_folder)
            else:
                relative_url = ''
            book_comments = get_book_comments(soup)
            book_genres = get_book_genres(soup)
            console_output(title, author, book_comments, book_genres)
            create_json_output(title, author, relative_url, book_comments, book_genres, folder=dest_folder)
        except (AttributeError, requests.RequestException) as err:
            print(f"Ошибка загрузки книги - {book_id}: {err}")


def console_output(title, author, book_comments, book_genres):
    print(f"Название: {title}\nАвтор: {author}")
    print("\nЖанр книги: ")
    for genre_link in book_genres:
        print(f"{genre_link.text}")
    print(f"\nКомментарии к книге: ")
    for comment in book_comments:
        print(f"{comment.text}")


def create_json_output(title, author, image_url, book_comments, book_genres, folder=None):
    books_info = {
        "title": title,
        "author": author,
        "img_src": image_url,
        "comments": [str(f"{comment.text}") for comment in book_comments],
        "genres": [str(f"{genre.text}") for genre in book_genres]
    }
    books_info_json = json.dumps(books_info, ensure_ascii=False, indent=4)
    filepath = os.path.join(folder, "books_info.json")
    with open(filepath, "a", encoding='utf8') as my_file:
        my_file.write(books_info_json)


def create_parser():
    parser = argparse.ArgumentParser(prog='parse_tululu_category',
                                     description='запускает скрипт для скачивания книг по категориям')
    parser.add_argument('--start_page', default=700,
                        help="Укажите начальную страницу с книгами для скачивания", type=int)
    parser.add_argument('--end_page', default=702,
                        help="Укажите конечную страницу с книгами для скачивания", type=int)
    parser.add_argument('--dest_folder', help="Выведет путь к каталогу с результатами",
                        type=str, default='books/')
    parser.add_argument('--skip_imgs', help="Для того,чтобы не скачивать картинки",
                        action='store_const', const=True)
    parser.add_argument('--skip_txt', help="Для того,чтобы не скачивать текст",
                        action='store_const', const=True)
    return parser


def main():
    Path("./books").mkdir(parents=True, exist_ok=True)
    parser = create_parser()
    parser_args = parser.parse_args()
    if parser_args.start_page and parser_args.end_page:
        for book_page in range(parser_args.start_page, parser_args.end_page):
            attempt = 0
            while True:
                try:
                    soup = fetch_catalog_page(book_page)
                    book_ids = extract_book_ids(soup)
                    download_all_book(book_ids, skip_txt=parser_args.skip_txt, skip_imgs=parser_args.skip_imgs,
                                      dest_folder=parser_args.dest_folder)
                    break
                except requests.ConnectionError as err:
                    print(f"Ошибка соединения для книги - {book_page} (попытка {attempt + 1}): {err}")
                    time.sleep(10)
                    attempt += 1
    if parser_args.dest_folder:
        print(f"Результаты хранятся в каталоге: {parser_args.dest_folder}")


if __name__ == "__main__":
    main()
