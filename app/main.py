#!/usr/bin/env python3

import subprocess
import sys

def run(title, cmd, shell=False):
    print(f"\n=== {title} ===")
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске: {e}")
        sys.exit(1)

def main():
    run("Получаем VPN‑конфиги", ["python3", "-m", "vpn.get_vpn_configs"])
    run("Подключаем VPN", ["python3", "-m", "vpn.connect_vpn"])
    run("Получаем ссылки", ["python3", "-m", "scraper.get_product_links"])
    print("=== Done ===")

if __name__ == "__main__":
    main()
