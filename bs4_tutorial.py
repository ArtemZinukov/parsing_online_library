import requests
from bs4 import BeautifulSoup



url = 'https://tululu.org/b5/'
response = requests.get(url)
response.raise_for_status()


soup = BeautifulSoup(response.text, 'lxml')

text = soup.find('div', {'id': 'content'}).find('h1').text
text_split = text.split(':')
# print(text_split[0])
# print(text_split[2].strip())
# comment = soup.find_all(class_="texts")
# for com in comment:
#     print(com.find(class_="black").text)
# print(comment)
genre = soup.find_all("span", class_="d_book")
for g in genre:
    for ga in g.find_all("a"):
        print(ga.text)

# print(genre)


def download_txt():
    pass
