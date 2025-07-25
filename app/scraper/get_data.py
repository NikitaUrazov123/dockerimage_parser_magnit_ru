import requests
import time
import logger
from datetime import date
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert
from utils import generate_id
from db_config import SQLALCHEMY_DATABASE_URL
from requests.exceptions import RequestException
import json

# -------------------------------------------------------------------------------------------------------
def get_product_name(html: str) -> str | None:
    soup = BeautifulSoup(html, 'html.parser')
    el = soup.find('span', attrs={'data-test-id': 'v-product-details-name'})
    return el.get_text(strip=True) if el else None

def get_current_price(html: str) -> float | None:
    soup = BeautifulSoup(html, 'html.parser')
    el = soup.find('span', attrs={'data-test-id': 'v-product-detail-price-current'})
    if el:
        clean = el.get_text(strip=True).replace('₽', '').strip()
        try: return float(clean)
        except ValueError: return None
    return None

def get_old_price(html: str) -> float | None:
    soup = BeautifulSoup(html, 'html.parser')
    el = soup.find('span', attrs={'data-test-id': 'v-product-detail-price-old'})
    if el:
        clean = el.get_text(strip=True).replace('₽', '').strip()
        try: return float(clean)
        except ValueError: return None
    return None

def get_product_parameters(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    for item in soup.select(".product-details-parameters-list__item"):
        name_el = item.select_one("[data-test-id='v-product-details-parameters-list-item-name']")
        value_el = item.select_one("[data-test-id='v-product-details-parameters-list-item-value']")
        if name_el and value_el:
            name = name_el.get_text(strip=True)
            value = value_el.get_text(strip=True)
            result[name] = value
    return result

# -------------------------------------------------------------------------------------------------------
HEADERS = {
    'Accept': '*/*',
    'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/95.0.4638.69 Safari/537.36')
}

engine = create_engine(SQLALCHEMY_DATABASE_URL)
metadata = MetaData(schema="online_market_monitoring")
magnit_data_table = Table("magnit_data", metadata, autoload_with=engine)

valid_columns = {col.name for col in magnit_data_table.columns}

with engine.begin() as conn:
    rows = conn.execute(
        text("SELECT id AS link_id, link FROM online_market_monitoring.magnit_links WHERE is_scraped = false")
    ).all()

for link_id, link in rows:
    logger.logging.info(f"Парсинг {link}")
    try:
        resp = requests.get(link, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        html = resp.text
    except RequestException as e:
        logger.logging.warning(f"Не удалось получить {link}: {e}")
        time.sleep(2)
        continue

    today_str = date.today().isoformat()
    
    record = {
        "record_id": generate_id(today_str, link),
        "link": link,
        "product_name": get_product_name(html),
        "current_price": get_current_price(html),
        "old_price": get_old_price(html),
        "product_parameters": get_product_parameters(html),
    }

    filtered_record = {k: v for k, v in record.items() if k in valid_columns}

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE online_market_monitoring.magnit_links SET is_scraped = true WHERE id = :id"),
            {"id": link_id}
        )

        stmt = insert(magnit_data_table).values(**filtered_record)
        stmt = stmt.on_conflict_do_nothing(index_elements=["record_id"])
        conn.execute(stmt)

    logger.logging.info(f"Записан {filtered_record.get('record_id')}")
    time.sleep(4)

logger.logging.info("=== Done ===")
