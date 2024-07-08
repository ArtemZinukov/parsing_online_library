import requests
from pathlib import Path


books_id = [32168, 32169, 32170, 123, 222, 32131, 4444, 51255, 55555, 72714]

Path("./books").mkdir(parents=True, exist_ok=True)
for book_id in books_id:
    url = f"https://tululu.org/txt.php?id={book_id}"
    response = requests.get(url)
    response.raise_for_status()

    filename = f'./books/book-{book_id}.txt'
    with open(filename, 'wb') as file:
        file.write(response.content)
