#!/usr/bin/env python3
"""mtg.py to list cards we want to buy
(env MTG_CHEAP=99 to adjust threshold)
"""
import datetime as DT
import os
import sys
import typing as T
from collections import namedtuple

import requests as HTTP
from bs4 import BeautifulSoup

MTG = namedtuple("MTG", "href name icon usd")

MAX = int(os.getenv("MTG_PAGES", "3"))
MIN = int(os.getenv("MTG_CENTS", "599"))
SEC = float(os.getenv("MTG_LIMIT", "10"))

URL = os.getenv("MTG_DOMAIN", "https://www.cardkingdom.com")
_UA = os.getenv(
    "MTG_AGENT",
    " ".join(
        [
            "Mozilla/5.0",
            "(Macintosh; Intel Mac OS X 10.15; rv:108.0)",
            "Gecko/20100101",
            "Firefox/108.0",
        ]
    ),
)


def login(email, password, agent=_UA, **kwargs) -> str:
    """two requests (GET and POST) to /customer_login
    (it's jank, but it works)
    """
    conn = HTTP.Session(**kwargs)
    data = {}
    head = {"User-Agent": agent}
    slow = 10  # seconds

    url = f"{URL}/customer_login"
    res = conn.get(url, timeout=SEC, headers=head)
    res.raise_for_status()
    #print(res.status_code, res.headers["Set-Cookie"])
    soup = BeautifulSoup(res.text, features="html.parser")
    for form in soup.find_all("form"):
        for item in form.find_all("input"):
            if item["type"] == "hidden":
                data[item["name"]] = item["value"]

    data["email"] = email
    data["password"] = password
    out = conn.post(url, timeout=slow, headers=head, data=data)
    out.raise_for_status()
    cookie = out.cookies['laravel_session']
    return cookie


def wishlist(agent=_UA, cheap=MIN, cookies=None, pages=MAX) -> None:
    """dump Card Kingdom summary = current inventory info, etc.
    from current wishlist (user ID'd by cookies, prices in USD)
    """

    def fetch_soup(url: str, slow: float = 10) -> BeautifulSoup:
        headers = {"Cookie": "; ".join(cookies or [])}
        headers["User-Agent"] = agent
        res = HTTP.get(url, headers=headers, timeout=slow)
        res.raise_for_status()
        return BeautifulSoup(res.text, features="html.parser")

    def parse_soup(row: BeautifulSoup) -> MTG:
        link = row.find_all("a")
        href = URL + link[0]["href"]
        name = link[0].text.strip()
        price = row.find("span", class_="price") or row
        stock = row.find("span", class_="stock") or row
        icon = "*" if stock.text.strip() == "In Stock" else "!"
        return MTG(icon=icon, href=href, name=name, usd=price.text.strip())

    def watch_list() -> T.Generator[MTG, None, None]:
        for page in range(pages):
            url = f"{URL}/myaccount/wishlist?page={page + 1}"
            for row in fetch_soup(url).find_all("div", class_="row"):
                card = parse_soup(row)
                yield card

    buys, sub, total = 0, 0, 0
    cards = list(watch_list())
    if not cards:
        raise ValueError("bad session or nothing in wishlist")
    print(" @ ", DT.datetime.now())
    for card in cards:
        print(f" {card.icon} {card.usd:>8s}: {card.name:36s} {card.href}")
        if card.icon == "*":
            cents = int(float(card.usd[1:]) * 100)
            if cents <= cheap:
                sub += cents
                buys += 1
            total += cents
    print(f" = ${sub/100} for {buys} <= ${cheap/100} vs. ${total/100} total")


def main(*args) -> int:
    """attempts login when necessary
    then, prints Card Kingdom wishlist
    """
    cookie = os.getenv("MTG_COOKIE", "")  # from login.py
    email, password = os.getenv("MTG_CREDENTIALS", ":").split(":")
    if len(args) >= 3:
        password = args[2]
    if len(args) >= 2:
        email = args[1]
    try:
        session_cookie = cookie or login(email, password)
        wishlist(cookies=[f"laravel_session={session_cookie}"])
    except (HTTP.HTTPError, Exception) as err:
        raise ValueError("login or GET wishlist failure") from err
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
