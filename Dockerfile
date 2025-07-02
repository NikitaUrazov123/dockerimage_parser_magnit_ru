FROM ubuntu:22.04

# Обновления и установка зависимостей
RUN apt-get update && apt-get install -y \
    openvpn \
    python3 \
    python3-pip \
    python3-venv \
    iproute2 \
    curl \
    sudo \
    && apt-get clean

# Создаём директорию под VPN-конфиги
RUN mkdir -p /etc/openvpn/configs

# Создаём виртуальное окружение
RUN python3 -m venv /opt/venv

# Активируем виртуальное окружение
ENV PATH="/opt/venv/bin:$PATH"

# Копируем скрипты внутрь контейнера
COPY get_vpn_configs.py /app/get_vpn_configs.py
COPY connect_vpn.sh /app/connect_vpn.sh
COPY requirments.txt /app/requirments.txt

# Установка зависимостей
RUN pip install --upgrade pip && pip install -r /app/requirments.txt

# Даём права на выполнение
RUN chmod +x /app/connect_vpn.sh

# Рабочая директория
WORKDIR /app

# Запускаем python и после него bash-скрипт
CMD ["bash", "-c", "python get_vpn_configs.py && ./connect_vpn.sh && tail -f /dev/null"]
