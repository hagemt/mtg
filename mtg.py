#!/usr/bin/env python3
"""mtg.py to list cards we want to buy
(env MTG_CENTS=99 to lower threshold)
USAGE: env "MTG_COOKIE=$(./mtg.py login --email ... <<< pass)" ./mtg,py cards
"""
# pylint: disable=missing-function-docstring
import argparse
import datetime as DT
import getpass as safe
import json
import os
import sys
import typing as T
from contextlib import contextmanager

import requests as HTTP
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # type: ignore

# environment variables:
# - MTG_PAGES=0   implies "page until we run out"
# - MTG_CENTS=599 implies <6 USD is a "cheap" card
# - MTG_LIMIT=10  implies HTTP RTT is <10s

# - MTG_AGENT="..." is User-Agent header for HTTP requests
# - MTG_COOKIE=... for pre-existing login (laravel_session)
# - MTG_DOMAIN=https://www.cardkingdom.com sets the base URL
# - MTG_FORMAT="" implies text/plain output (vs. csv/json)
# - MTG_SECRET="username@example.com" + ":" + "password"
# see login function or details re: how cookies work
MAX = int(os.getenv("MTG_PAGES", "0"))
MIN = int(os.getenv("MTG_CENTS", "599"))
SEC = float(os.getenv("MTG_LIMIT", "10"))

FMT = os.getenv("MTG_FORMAT", "")  # raw log vs. csv/json
URL = os.getenv("MTG_DOMAIN", "https://www.cardkingdom.com")
# curl's default User-Agent is banned; use Firefox's:
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


def login(email: str, password: str, **kwargs) -> str:
    """two requests (GET and POST) to /customer_login
    N.B. a laravel_session is still returned even given bad credentials
    (an empty string is returned for HTTP failures)
    """
    try:
        agent = {"User-Agent": _UA}
        inputs = {}
        slow = SEC
        with HTTP.Session(**kwargs) as conn:
            url = f"{URL}/customer_login"
            res = conn.get(url, timeout=slow, headers=agent)
            # print(res.status_code, res.headers["Set-Cookie"])
            res.raise_for_status()

            soup = BeautifulSoup(res.text, features="html.parser")
            for form in soup.find_all("form"):
                for item in form.find_all("input"):
                    if item["type"] == "hidden":
                        inputs[item["name"]] = item["value"]

            inputs["email"] = email
            inputs["password"] = password
            out = conn.post(url, timeout=slow, headers=agent, data=inputs)
            out.raise_for_status()

            return out.cookies["laravel_session"]
    except HTTP.HTTPError as err:
        print(f"--- during login: {err}", file=sys.stderr)
        return ""


class Card(T.NamedTuple):
    """models the Card Kingdom entity"""

    href: str
    name: str
    icon: str
    usd: str

    @property
    def json(self) -> dict:
        return {
            "href": self.href,
            "name": self.name,
            "usd": self.usd,
            "out": self.icon == "!",
        }


class Format:
    """handles what to print out

    formats include csv/json/etc.
    """

    def __init__(self, cheap=MIN, writer=FMT):
        self.counts = [0, 0, 0, cheap]
        self.visited = []
        self.writer = writer.lower() or "text"

    @staticmethod
    def money(cents: int) -> str:
        return f"{cents/100:01.2f}"

    def header(self) -> None:
        if self.writer == "csv":
            print(",".join(("icon", "usd", "name", "href")))
            return
        if self.writer == "json":
            return
        print("# executed @", DT.datetime.now(), file=sys.stderr)

    def footer(self) -> None:
        buy = self.counts[0]
        inf = Format.money(self.counts[1])
        sup = Format.money(self.counts[2])
        mid = Format.money(self.counts[3])
        out = f"# ${inf} for N={buy} <= ${mid}=M vs. ${sup} total"
        if self.writer == "json":
            print(json.dumps({"//": out, "wishlist": self.visited}))
        else:
            print(out, file=sys.stderr)

    def visit(self, card: Card) -> None:
        cost = card.usd
        cents = int(float(cost[1:]) * 100)
        cheap = cents < self.counts[3]
        later = card.icon != "*"
        if not later:
            if cheap:
                self.counts[0] += 1
                self.counts[1] += cents
            self.counts[2] += cents
        if self.writer == "csv":
            prefix = "OUT" if later else "BUY" if cheap else "USD"
            name = card.name
            href = card.href
            print(",".join(f"'{s}'" for s in (prefix, cost, name, href)))
        elif self.writer == "json":
            self.visited.append(card.json)
        else:
            print(f" {card.icon} {cost:>8s}: {card.name:36s} {card.href}")

    @classmethod
    @contextmanager
    def visitor(cls):
        fmt = cls()
        fmt.header()
        yield fmt.visit
        fmt.footer()


def dump(agent=_UA, cookies=None, pages=MAX) -> None:
    """dump Card Kingdom summary = current inventory info, etc.
    from current wishlist (user ID'd by cookies, prices in USD)
    """

    def fetch_soup(url: str, slow: float = 10) -> BeautifulSoup:
        headers = {"Cookie": "; ".join(cookies or [])}
        headers["User-Agent"] = agent
        res = HTTP.get(url, headers=headers, timeout=slow)
        res.raise_for_status()
        return BeautifulSoup(res.text, features="html.parser")

    def parse_soup(row: BeautifulSoup) -> Card:
        link = row.find_all("a")
        href = URL + link[0]["href"]
        name = link[0].text.strip()
        price = row.find("span", class_="price") or row
        stock = row.find("span", class_="stock") or row
        icon = "*" if stock.text.strip() == "In Stock" else "!"
        return Card(icon=icon, href=href, name=name, usd=price.text.strip())

    def watch_list(max_pages: int = 10) -> T.Generator[Card, None, None]:
        for page in range(pages if pages > 0 else max_pages):
            url = f"{URL}/myaccount/wishlist?page={page + 1}"
            rows = fetch_soup(url).find_all("div", class_="row")
            if not rows:
                return
            for row in rows:
                card = parse_soup(row)
                yield card

    cards = list(watch_list())
    if not cards:
        raise ValueError("bad session or nothing in wishlist")
    with Format.visitor() as visit:
        for card in cards:
            visit(card)


def pii(desc: str) -> str:
    return safe.getpass(prompt=f"Card Kingdom {desc}: ")


def parse(secret: str, cookie: str) -> T.Tuple[str, str, str]:
    email, *split = secret.split(":")
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("action", choices=["cards", "login"])
    parser.add_argument("--email", required=False)
    args = parser.parse_args()

    if args.action == "login":
        print(secret, cookie, email, args)
        username = args.email or email or pii("email is")
        password = split[0] if split else pii("password")
        return args.action, username, password
    if not cookie:
        raise ValueError("missing MTG_COOKIE or MTG_SECRET for login")
    return "cards", "", ""


def main(*argv) -> int:
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    first = argv[0] if argv else "mtg.py"
    usage = f'USAGE: env MTG_COOKIE="$(./{first} login)" ./{first}'
    cookie = os.getenv("MTG_COOKIE", "")  # previous login
    secret = os.getenv("MTG_SECRET", ":")
    try:
        action, email, password = parse(secret, cookie)
    except ValueError as err:
        print(f"--- {err}; {usage}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 1
    if action == "login":
        print(login(email, password))
        return 0
    if action != "cards":
        print(usage, file=sys.stderr)
        return 1
    try:
        session_cookie = cookie or login(email, password)
        dump(cookies=[f"laravel_session={session_cookie}"])
    except (HTTP.ConnectionError, ValueError) as err:
        print(f"--- CK wishlist failure: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
