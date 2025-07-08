# utils.py
import hashlib

def generate_id(date_str: str, link: str) -> str:
    raw = f"{date_str}{link}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()
