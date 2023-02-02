#!/usr/bin/env python3
"""USAGE: env MTG_COOKIE="$(./login.py)" ./mtg.py # or ./mtg.py [email] [pass]

(to scrape all cards off your wishlist, after doing Card Kingdom login once)
"""
import getpass as safe
import os
import sys

import requests as HTTP
from bs4 import BeautifulSoup
from dotenv import load_dotenv


def main(*args) -> int:
    """attempt GET + POST /customer_login
    (to obtain the laravel_session cookie)
    """
    def login(email, password, agent="Mozilla/5.0", **kwargs) -> str:
        conn = HTTP.Session(**kwargs)
        data = {}
        head = {"User-Agent": agent}
        slow = 10  # seconds

        url = "https://www.cardkingdom.com/customer_login"
        res = conn.get(url, timeout=slow, headers=head)
        res.raise_for_status()
        #print(res.status_code, res.headers["Set-Cookie"])
        soup = BeautifulSoup(res.text, features="html.parser")
        for form in soup.find_all("form"):
            for item in form.find_all("input"):
                if item["type"] == "hidden":
                    data[item["name"]] = item["value"]

        data["email"] = email if len(args) < 2 else args[1]
        data["password"] = password if len(args) < 3 else args[2]
        out = conn.post(url, timeout=slow, headers=head, data=data)
        out.raise_for_status()
        return out.cookies['laravel_session']

    try:
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        email, *rest = os.getenv("MTG_CREDENTIALS", ":").split(":")
        password = rest[0] if rest else ""

        prompt = f"--- Card Kingdom password for {email}: "
        cookie = login(email, password or safe.getpass(prompt=prompt))
        print(cookie)
        return 0
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
