# crontab (mini)

After:

```
git clone git@github.com:hagemt/mtg.git ~/.cardkingdom
```

Just `crontab -e` for:

```
 0 22 * * * /Users/teh/.unicornleap/unicornleap
 0 23 * * * /Users/teh/.unicornleap/unicornleap -n 2
 0  0 * * * /Users/teh/.unicornleap/unicornleap -n 3
 0  1 * * * /Users/teh/.unicornleap/unicornleap -n 5
 0  2 * * * /Users/teh/.unicornleap/unicornleap --herd

 0 * * * * /Users/teh/.cardkingdom/mtg.sh
```

That bottom line (every hour on the hour)
