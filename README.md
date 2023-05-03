## G2.com scrapper to scrap categories and single posts

This scrapper scrap the first 30 posts for each category and save to the database

Postgres database is used you can change the config in db.py file.


## Fetch categories
```sh
python main.py fetch-categories
```

## Fetch Item Links in each category
```sh
python main.py fetch-item-links
```

## Fetch Items from each item link scraped
```sh
python main.py fetch-items
```

## Fetch Item prices from each item link scraped and map agains item_id in database
```sh
python main.py fetch-item-prices
```


