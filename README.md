# in .env: MTG_SECRET="email:password"

tl;dr: To pull your wishlist from Card Kingdom...

```
git clone git@github.com:hagemt/mtg.git ~/.cardkingdom
```

Run `crontab -e` to add:

```
0 * * * * $HOME/.cardkingdom/wish.sh
```

For `log/mtg_wishlist_YYYY-mm-ddTHH_MM_SS.log` every hour on the hour.

## Python scripts

If you want to write your own scraper, take a look at `./login.py` first.

That has a function similar to `./mtg.py` for obtaining the session cookie.

## Wishlist

There's other Card Kingdom functionality to add, but this is OK to start.

I'd like "cart optimization" routines (aware of Show All Versions, etc.)

Ideally, it would draw from my wishlist and auto-build/buy ~$35 for me.
