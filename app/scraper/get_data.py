import requests
import time
import logging
from datetime import date
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert
from utils import generate_id
from db_config import SQLALCHEMY_DATABASE_URL
from requests.exceptions import RequestException

# -------------------------------------------------------------------------------------------------------
def get_product_name(text: str) -> str | None:
    soup = BeautifulSoup(text, 'html.parser')
    el = soup.find('span', attrs={'data-test-id': 'v-product-details-name'})
    return el.get_text(strip=True) if el else None

def get_current_price(text: str) -> float | None:
    soup = BeautifulSoup(text, 'html.parser')
    el = soup.find('span', attrs={'data-test-id': 'v-product-detail-price-current'})
    if el:
        raw_string = el.get_text(strip=True)
        clean = raw_string.replace('₽', '').strip()
        try:
            return float(clean)
        except ValueError:
            return None
    return None

def get_old_price(text: str) -> float | None:
    soup = BeautifulSoup(text, 'html.parser')
    el = soup.find('span', attrs={'data-test-id': 'v-product-detail-price-old'})
    if el:
        raw_string = el.get_text(strip=True)
        clean = raw_string.replace('₽', '').strip()
        try:
            return float(clean)
        except ValueError:
            return None
    return None
# -------------------------------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HEADERS = {
    'Accept': '*/*',
    'user-agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        ' AppleWebKit/537.36 (KHTML, like Gecko)'
        ' Chrome/95.0.4638.69 Safari/537.36'
    )
}

engine = create_engine(SQLALCHEMY_DATABASE_URL)
metadata = MetaData(schema="online_market_monitoring")
magnit_data_table = Table("magnit_data", metadata, autoload_with=engine)

valid_columns = {col.name for col in magnit_data_table.columns}

today_str = date.today().isoformat()

with engine.begin() as conn:
    rows = conn.execute(
        text("SELECT id AS link_id, link FROM online_market_monitoring.magnit_links WHERE is_scraped = false")
    ).all()

for link_id, link in rows:
    logging.info(f"Парсинг {link}")
    try:
        resp = requests.get(link, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        html = resp.text
    except RequestException as e:
        logging.warning(f"Не удалось получить {link}: {e}")
        time.sleep(2)
        continue

    record = {
        "record_id":    generate_id(today_str, link),
        "link":         link,
        "product_name": get_product_name(html),
        "current_price":get_current_price(html),
        "old_price":    get_old_price(html),
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

    logging.info(f"Запись {filtered_record.get('record_id')}")
    time.sleep(3)

logging.info("=== Done ===")
