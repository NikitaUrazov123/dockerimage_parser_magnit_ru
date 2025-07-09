from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import pandas as pd
import requests
import time
from datetime import date
import logger
from db_config import SQLALCHEMY_DATABASE_URL
from utils import generate_id
from bs4 import BeautifulSoup

# -------------------------------------------------------------------------------------------------------
def get_last_page_number(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    li_tag = soup.find('li', attrs={'data-test-id': 'v-pagination-pages-count'})
    if li_tag:
        text = li_tag.get_text(strip=True)
        if text.isdigit():
            return int(text)
        else:
            numbers = ''.join(filter(str.isdigit, text))
            return int(numbers) if numbers else 1
    return 1

def get_product_links(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    product_links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/product/'):
            clean_href = href.split('?')[0]
            product_links.add(clean_href)
    return list(product_links)
# -------------------------------------------------------------------------------------------------------
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
    logger.logging.info(f"{page_url}")

    product_links = [DOMAIN_NAME + link for link in get_product_links(page_url)]
    
    df = pd.DataFrame({
        'date': [date.today()] * len(product_links),
        'link': product_links
        })
    
    df['id'] = df.apply(lambda row: generate_id(row['date'], row['link']), axis=1)
    
    df = df.drop_duplicates(subset=['id'])

    with engine.begin() as conn:
        for row in df.to_dict(orient='records'):
            stmt = insert(magnit_links_table).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)

    time.sleep(2)
