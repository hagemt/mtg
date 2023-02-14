#!/usr/bin/env python3
"""USAGE: put MTG_SECRET in .env file + export MTG_COOKIE="$(./login.py)"

see also: ./mtg.py
"""
import getpass as ask
import os
import sys

import requests as HTTP
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # type: ignore

# Card Kingdom refuses curl/requests's User-Agent, but this one works:
ck_site = os.getenv("MTG_BASE_URL", "https://www.cardkingdom.com")
headers = {"User-Agent": os.getenv("MTG_AGENT", "Mozilla/5.0")}
timeout = float(os.getenv("MTG_LIMIT", "10.0"))

check_url = f"{ck_site}/myaccount/profile"
login_url = f"{ck_site}/customer_login"


def main(*args) -> int:
    """attempt GET + POST /customer_login
    (to obtain the laravel_session cookie)
    """

    def login(email: str, password: str, **kwargs) -> dict:
        with HTTP.Session(**kwargs) as conn:
            data = {}

            url = login_url
            one = conn.get(url, timeout=timeout, headers=headers)
            one.raise_for_status()
            # print(res.status_code, res.headers["Set-Cookie"])
            soup = BeautifulSoup(one.text, features="html.parser")
            for form in soup.find_all("form"):
                for item in form.find_all("input"):
                    if item["type"] == "hidden":
                        data[item["name"]] = item["value"]

            data["email"] = email
            data["password"] = password
            two = conn.post(url, timeout=timeout, headers=headers, data=data)
            two.raise_for_status()
            return dict(two.cookies)

    def check(**kwargs) -> bool:
        res = HTTP.get(check_url, timeout=timeout, headers=headers, **kwargs)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, features="html.parser")
        # no forms mean the site doesn't need us to Sign In
        return not soup.find_all("form")

    def setup(filename: str) -> str:
        dotenv_path = os.path.dirname(__file__)
        dotenv_path = os.path.join(dotenv_path, filename)
        dotenv_path = os.path.normpath(dotenv_path)
        load_dotenv(dotenv_path)
        return dotenv_path

    try:
        # import datetime as DT, logging
        # logging.basicConfig(level=logging.DEBUG)
        # print(f"--- {DT.datetime.now()}:", *args, file=sys.stderr)
        # breakpoint()
        myenv = setup(os.getenv("MTG_DOTENV", ".env"))
        first, *split = os.getenv("MTG_SECRET", ":").split(":")
        other = split[0] if split else ""
        if not first or not other:
            print(f"--- no MTG_SECRET set ({myenv})", file=sys.stderr)

        email = first or ask.getpass("--- Card Kingdom email address: ")
        prompt = f"--- Card Kingdom password for {email}: "
        password = other or ask.getpass(prompt=prompt)
        session = login(email, password)

        if check(cookies=session):  # ensures MTG_COOKIE will work
            with open(myenv, encoding="UTF-8", mode="a") as env:
                print(f'export MTG_SECRET="{email}:{password}"', file=env)
            print(session.get("laravel_session", ""))
        else:
            print(f"--- CK rejects {email}:password", file=sys.stderr)
            print(session.get("laravel_session", ""), file=sys.stderr)

        return 0
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
