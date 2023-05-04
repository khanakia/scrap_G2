import json
from math import prod
import re
import time
from typing import Any, cast
from bs4 import BeautifulSoup, Tag
import requests
import db
from urllib.parse import urlparse
from sqlalchemy.sql import text,column
from shared import get_request, make_decimal
import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from sqlalchemy.dialects import postgresql

conn = db.get_connection()

def fetch_and_save_categories():
    response = requests.get('https://www.g2.com/categories/mega_menu.json')
    data = response.json()
    for c in data:
        slug = urlparse(c['url']).path.split('/')[-1]

        cat = db.session.query(db.Category).filter_by(ext_id=c["id"]).first()
        if cat:
            return;

        ins = db.Category.insert().values(
            name=c["name"],
            ext_id=c["id"],
            ext_url=c["url"],
            slug=slug,
        )
        result = conn.execute(ins)
        cid = result.inserted_primary_key[0]

        if "children" in c:
            for sc in c["children"]:
                print("--"+sc['name'])
                slug = urlparse(sc['url']).path.split('/')[-1]
                ins = db.Category.insert().values(
                    name=sc["name"],
                    ext_id=sc["id"],
                    ext_url=sc["url"],
                    slug=slug,
                    parent_id=cid
                )
                result = conn.execute(ins)

# won't work as cloudflare blocks the page
def fetch_product_links_in_category(main_source_url):
    """
    function made to extract all category
    links from the data source url
    """
    
    links = []

    req = get_request(main_source_url)
    if req == None:
        print("isue")
        return "issue makeing reqest, no links generated"
    else:
        print("parsing category")
        soup = BeautifulSoup(req, "html.parser")
        product_container = soup.select_one("#product-cards")

        # print(product_container)
        if product_container is None:
            print("product_container is none")
            return
        product_cards = product_container.find_all("div", {"class": "product-card"})
        for product in product_cards:
            try:
                name_node = product.select_one("div.product-card__product-name > a")
                # print(name_node["href"])
                links.append(name_node["href"])
            
            except:
                print("some error")
    return links


# this func will extract the single product page links fromt the category page source which we will pass using headless
def extract_product_links_from_category_page_source(source: str, category_id: int):
    links = []

    print("extracting links from category page source", category_id)
    soup = BeautifulSoup(source, "html.parser")
    product_container = soup.select_one("#product-cards")

    # print(product_container)
    if product_container is None:
        print("product_container is none")
        return
    product_cards = product_container.find_all("div", {"class": "product-card"})
    for product in product_cards:
        try:
            name_node = product.select_one("div.product-card__product-name > a")
            # print(name_node["href"])
            links.append({
                "url": name_node["href"],
                "category_id": category_id
            })
        
        except:
            print("some error")
        
    return links


# it will loop through all the categories in database and extract the product links and build the links table
def get_item_links_from_categories_and_save():
    cats = db.session.query(db.Category).filter(db.Category.parent_id.isnot(None)).order_by(text("id asc")).offset(0).limit(10000).all()
    options = uc.ChromeOptions() 
    options.headless = False 
    driver = uc.Chrome(use_subprocess=True, options=options) 
    wait = WebDriverWait(driver, 10)
    for cat in cats:
        print("parsing category page", cat.name, cat.id)
        try :
            driver.get(cat.ext_url)
            wait.until_not(EC.title_is('Just a moment...'))
        except TimeoutException as e:
            print("Page load Timeout Occured ... moving to next item !!!")
        
        source = driver.page_source
        links = extract_product_links_from_category_page_source(source, cat.id)
        
        if(links is  None or len(links) == 0):
            continue
        print(json.dumps(links, indent=3))
        db.session.bulk_insert_mappings(db.Link, links)
        db.session.commit()


def extract_item_data_from_page_source(source: str):
    # setting default values to prevent error in db.insert sqlachemy undefined values
    product = {
        "website_link": "",
        "logo_url": "",
        "descr": "",
        "name": "",
        "ratings_count": 0,
        "reviews_count": 0
    }

    soup = BeautifulSoup(source, "html.parser")
    # print (soup.title.get_text())

    try:
        websites = soup.find_all(text=re.compile('Company Website'))
        divs = [website.parent for website in websites]
        product['website_link'] = divs[0].find_next_sibling('a')['href']
    except:
        pass

    try:
        descr = soup.find("div", itemprop="description")
        product['descr'] = cast(Tag, descr).get_text()
    except:
        pass

    headtitle = soup.select_one(".product-head__title a")
    if headtitle is not None:
        product['name'] = headtitle.text
        
    logo = soup.find("meta", attrs={'property': 'og:image'})
    product['logo_url'] = cast(Tag, logo).get('content')

    aggregateRating = soup.find("span", itemprop="aggregateRating")
   
    if aggregateRating is not None:
        # itemReviewed = cast(Tag, aggregateRating).find("meta", itemprop="itemReviewed")
        # if itemReviewed is not None and hasattr(itemReviewed, 'get'):
        #     product['name'] = cast(Tag, itemReviewed).get('content')

        rating = cast(Tag, aggregateRating).find("meta", itemprop="ratingValue")
        if rating is not None and hasattr(rating, 'get'):
            product['ratings_count'] = float(cast(Any, rating).get('content'))

        reviewCount = cast(Tag, aggregateRating).find("meta", itemprop="reviewCount")
        if reviewCount is not None and hasattr(reviewCount, 'get'):
            product['reviews_count'] = int(cast(Any, reviewCount).get('content'))


    return product

# get the product links from the database table lnks and fetch each product and then save to items table
def fetch_links_and_save_as_items():
    links = db.session.query(db.Link).order_by(text("id asc")).offset(0).limit(745).all()
    options = uc.ChromeOptions() 
    options.headless = False 
    driver = uc.Chrome(use_subprocess=True, options=options) 
    wait = WebDriverWait(driver, 10)
    for link in links:
        print("parsing product link page", link.id, link.url)
        try :
            driver.get(link.url)
            WebDriverWait(driver, timeout=10).until(
                EC.visibility_of_element_located((By.ID, "details"))
            )

        except TimeoutException as e:
            print("Page load Timeout Occured ... moving to next item !!!")

        source = driver.page_source
        product = extract_item_data_from_page_source(source)
        
        print(json.dumps(product, indent = 3))
        # continue

        item = db.session.query(db.Item).filter_by(link_id=link.id).first()
        if item is None:
            # item = db.Item(**product)
            item = db.Item()

        item.slug = urlparse(link.url).path.split('/')[-2]
        item.category_id = link.category_id
        item.link_id = link.id
        item.name = product['name']
        item.descr = product['descr']
        item.logo_url  = product['logo_url']
        item.reviews_count = product['reviews_count']
        item.ratings_count = product['ratings_count']
        item.website_link = product['website_link']

        db.session.add(item)
        db.session.commit()



def extract_prices_data_from_page_source(source: str, item_id: int):
    prices = []
    soup = BeautifulSoup(source, "html.parser")
    sapp = soup.select_one("table.editions")
    if sapp is not None:
        pspecs = sapp.select("tr.editions__tr")
        for pspec in pspecs:
            price = 0
            pricenode = pspec.select_one(".editions__price")
            if pricenode is not None:
                # price = make_decimal(pricenode.text[1:])
                price = pricenode.text
            
            name = ''
            name_node = pspec.select_one(".editions__name")
            if name_node is not None:
                name = name_node.text

            unit_text = ''
            unit_text_node = pspec.select_one(".editions__per")
            if unit_text_node is not None:
                unit_text = unit_text_node.text
            # print(price, name, unit_text)
            prices.append({
                "name": name,
                "price": price,
                "unit_text": unit_text,
                "item_id": item_id,
                "currency": "USD"
            })

    return prices

# get the product links from the database table lnks and fetch each product and then save to items table
def fetch_item_prices_and_save():
    items = db.session.query(db.Item, db.Link).filter(db.Item.link_id == db.Link.id).order_by(text("items.id asc")).offset(0).limit(10000).all()
    options = uc.ChromeOptions() 
    options.headless = False 
    driver = uc.Chrome(use_subprocess=True, options=options) 
    # wait = WebDriverWait(driver, 10)
    for item, link in items:
        url = link.url[:link.url.rfind('/')]+"/pricing"
        print("parsing product price page", item.id, url)
        try :
            driver.get(url)
            WebDriverWait(driver, timeout=10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "product-head"))
            )
        except TimeoutException as e:
            print("Page load Timeout Occured ... moving to next item !!!")
        
        source = driver.page_source
        prices = extract_prices_data_from_page_source(source, item.id)
        print(prices)
       
        if(prices is  None or len(prices) == 0):
            continue
        print(json.dumps(prices, indent=3))
        db.session.bulk_insert_mappings(db.Price, prices)
        db.session.commit()