import argparse
import os
import time
import json

import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tululu_parsing_functions import fetch_book_page, get_author_and_title, get_image
from tululu_parsing_functions import get_book_comments, get_book_genres, download_txt, download_image

URL = "https://tululu.org"


def fetch_catalog_page(page_number):
    url_catalog_page = f"https://tululu.org/l55/{page_number}/"
    response = requests.get(url_catalog_page)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def extract_book_ids(soup):
    content_div = soup.select(".bookimage a")
    book_ids = []
    for content in content_div:
        relative_url = content["href"]
        relative_url_parts = urlparse(relative_url)
        book_ids.append(relative_url_parts.path.split("/b")[1])
    return book_ids


def download_all_book(book_id, dest_folder, skip_txt=False, skip_imgs=False):
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
    return title, author, relative_url, book_comments, book_genres


def parse_book_page(title, author, relative_url, book_comments, book_genres):
    book_details = {
        "title": title,
        "author": author,
        "img_src": relative_url,
        "comments": [str(f"{comment.text}") for comment in book_comments],
        "genres": [str(f"{genre.text}") for genre in book_genres]
    }
    return book_details


def console_output(title, author, book_comments, book_genres):
    print(f"Название: {title}\nАвтор: {author}")
    print("\nЖанр книги: ")
    for genre_link in book_genres:
        print(f"{genre_link.text}")
    print(f"\nКомментарии к книге: ")
    for comment in book_comments:
        print(f"{comment.text}")


def create_json_output(books_info, folder=None):
    filepath = os.path.join(folder, "books_info.json")
    with open(filepath, "w", encoding='utf8') as file:
        json.dump(books_info, file, ensure_ascii=False, indent=4)


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
                        action='store_true')
    parser.add_argument('--skip_txt', help="Для того,чтобы не скачивать текст",
                        action='store_true')
    return parser


def main():
    Path("./books").mkdir(parents=True, exist_ok=True)
    parser = create_parser()
    parser_args = parser.parse_args()
    books_details = []
    for book_page in range(parser_args.start_page, parser_args.end_page):
        attempt = 0
        while True:
            try:
                soup = fetch_catalog_page(book_page)
                book_ids = extract_book_ids(soup)
                for book_id in book_ids:
                    try:
                        title, author, relative_url, book_comments, book_genres = (
                            download_all_book(book_id, skip_txt=parser_args.skip_txt,
                                              skip_imgs=parser_args.skip_imgs,
                                              dest_folder=parser_args.dest_folder))
                        book_details = parse_book_page(title, author, relative_url, book_comments, book_genres)
                        books_details.append(book_details)
                        console_output(title, author, book_comments, book_genres)
                    except (AttributeError, requests.RequestException) as err:
                        print(f"Ошибка загрузки книги - {book_id}: {err}")

                break
            except requests.ConnectionError as err:
                print(f"Ошибка соединения для книги - {book_page} (попытка {attempt + 1}): {err}")
                time.sleep(10)
                attempt += 1
    create_json_output(books_details, folder=parser_args.dest_folder)
    print(f"Результаты хранятся в каталоге: {parser_args.dest_folder}")


if __name__ == "__main__":
    main()
