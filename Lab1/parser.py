import re
import time
import requests
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

URL = "https://auto.drom.ru/spb/used/all/"
LIMIT = 1000
MAX_PAGES = 60
PAUSE = 15
WAIT = 120
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def search(pattern, text):
    m = re.search(pattern, text)
    return m.group(1) if m else None


def number(value):
    return int(re.sub(r"\D", "", value)) if value else None


def parse_card(h3):
    link = h3.find_parent("a") or h3.find("a")
    if link is None:
        return None

    card = h3
    while "₽" not in card.get_text():
        card = card.parent
        if card is None or len(card.find_all("h3")) > 1:
            return None

    title = h3.get_text(strip=True)
    own = list(h3.stripped_strings)
    text = " ".join(s for s in card.stripped_strings if s not in own)

    volume = search(r"(\d\.\d)\s*л(?!\.)", text)
    return {
        "name": title.split(",")[0],
        "year": number(search(r"(\d{4})$", title)),
        "price": number(search(r"(\d[\d\s]*)₽", text)),
        "volume_l": float(volume) if volume else None,
        "power_hp": number(search(r"(\d+)\s*л\.с\.", text)),
        "fuel": search(r"\b(бензин|дизель|гибрид|электро|газ)\b", text),
        "transmission": search(r"\b(механика|АКПП|вариатор|робот|редуктор)\b", text),
        "drive": search(r"\b(передний|задний|4WD)\b", text),
        "mileage_km": number(search(r"(\d[\d\s]*)км", text)),
        "url": urljoin(URL, link["href"]),
    }


cars = {}
page = 1
while len(cars) < LIMIT and page <= MAX_PAGES:
    url = URL if page == 1 else f"{URL}page{page}/"

    for attempt in range(3):
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 429:
            break
        print(f"Страница {page}: 429")
        time.sleep(WAIT)
    if response.status_code != 200:
        print("Ошибка", response.status_code)
        break
    response.encoding = "windows-1251"

    soup = BeautifulSoup(response.text, "html.parser")
    found = [parse_card(h3) for h3 in soup.find_all("h3")]
    found = [car for car in found if car]
    if not found:
        print("Объявления не найдены")
        break

    for car in found:
        cars[car["url"]] = car
    print(f"Страница {page}: собрано {len(cars)}")

    pd.DataFrame(list(cars.values())).head(LIMIT).to_csv("drom_spb.csv", index=False, encoding="utf-8-sig")
    page += 1
    time.sleep(PAUSE)

df = pd.DataFrame(list(cars.values())).head(LIMIT)
print(f"Готово: {len(df)} объявлений")