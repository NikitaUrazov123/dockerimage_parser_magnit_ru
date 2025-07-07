#!/bin/bash
set -e

echo "Получаем VPN-конфиги..."
python3 /app/get_vpn_configs.py

echo "Подключаем VPN..."
/app/connect_vpn.sh

echo "Получаем ссылки с сайта..."
python3 /app/get_product_links.py

echo "Done"
