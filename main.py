import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

books_id = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
URL = "https://tululu.org"


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError("Redirect")
    return response


def get_author_and_title(url, book_id):
    url_book = f"{url}/b{book_id}/"
    response = requests.get(url_book)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    content_div = soup.find('div', {'id': 'content'})
    if content_div:
        h1_tag = content_div.find('h1')
        if h1_tag:
            text = h1_tag.text
            text_split = text.split(':')
            title = text_split[0].strip()
            author = text_split[2].strip()
            return title, author
    return None, None


def download_txt(url, filename, folder='books/'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f"{filename}.txt")
    response = requests.get(url)
    response = check_for_redirect(response)
    with open(filepath, 'wb') as file:
        file.write(response.content)


Path("./books").mkdir(parents=True, exist_ok=True)
for book_id in books_id:
    download_url = f"{URL}/txt.php?id={book_id}"
    try:
        filename, author = get_author_and_title(URL, book_id)
        download_txt(download_url, filename, folder='books/')

    except requests.RequestException:
        print(f"Ошибка при запросе книги {book_id}")

