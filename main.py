import requests
from pathlib import Path


books_id = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError("Redirect")
    return response


Path("./books").mkdir(parents=True, exist_ok=True)
for book_id in books_id:
    url = f"https://tululu.org/txt.php?id={book_id}"
    try:
        response = requests.get(url)
        response = check_for_redirect(response)
        filename = f'./books/book-{book_id}.txt'
        with open(filename, 'wb') as file:
            file.write(response.content)
    except requests.RequestException:
        print(f"Ошибка при запросе книги {book_id}")

