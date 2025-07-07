from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import pandas as pd
import requests
import re
import time
from datetime import date
import logging
from db_config import SQLALCHEMY_DATABASE_URL

# -------------------------------------------------------------------------------------------------------
def get_last_page_number(url):
    response = requests.get(url, headers=HEADERS, timeout=5)
    html_text = response.text

    outer_pattern = r'<li[^>]*data-test-id="v-pagination-pages-count"[^>]*>.*?</li>'
    outer_match = re.search(outer_pattern, html_text, re.DOTALL)

    if outer_match:
        block = outer_match.group(0)
        inner_pattern = r'<!--\[\s*-->(\d+)\s*<!--\]-->'
        inner_match = re.search(inner_pattern, block)
        return int(inner_match.group(1)) if inner_match else 1
    return 1

# -------------------------------------------------------------------------------------------------------
def get_product_links(url):
    response = requests.get(url, headers=HEADERS, timeout=5)
    html_text = response.text
    pattern = r'/product\/[^?"]+'
    return re.findall(pattern, html_text)

# -------------------------------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HEADERS = {
    'Accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
}

DOMAIN_NAME = 'https://magnit.ru'
MAIN_PAGE_LINK = '/catalog/7485-detskie_tovary_'

# -------------------------------------------------------------------------------------------------------
engine = create_engine(SQLALCHEMY_DATABASE_URL)
metadata = MetaData(schema='online_market_monitoring')
magnit_links_table = Table('magnit_links', metadata, autoload_with=engine)


for page_num in range(1, get_last_page_number(DOMAIN_NAME + MAIN_PAGE_LINK) + 1):
    page_url = f'{DOMAIN_NAME}{MAIN_PAGE_LINK}?page={page_num}'
    logging.info(f"---------{page_url}---------")

    product_links = [DOMAIN_NAME + link for link in get_product_links(page_url)]

    df = pd.DataFrame({
        'date': [date.today()] * len(product_links),
        'link': product_links
    }).drop_duplicates(subset=['date', 'link'])

    with engine.begin() as conn:
        for row in df.to_dict(orient='records'):
            stmt = insert(magnit_links_table).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)

    time.sleep(2)
