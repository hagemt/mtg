# in .env: MTG_SECRET="email:password"

To pull your wishlist regularly:

```
git clone git@github.com:hagemt/mtg.git ~/.cardkingdom
```

Just `crontab -e` with:

```
0 * * * * $HOME/.cardkingdom/mtg.sh
```

For `logs` every hour on the hour.
