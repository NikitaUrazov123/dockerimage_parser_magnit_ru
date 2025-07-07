FROM ubuntu:22.04

# Отключаем интерактивные диалоги у apt и задаём часовой пояс
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Minsk

# Добавляем PPA для Python 3.11
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update

# Установка зависимостей и Python 3.11
RUN apt-get install -y \
    tzdata \
    openvpn \
    python3.11 \
    python3.11-venv \
    python3.11-distutils \
    python3-pip \
    iproute2 \
    curl \
    sudo \
  && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
  && dpkg-reconfigure --frontend noninteractive tzdata \
  && apt-get clean

# Создаём директорию под VPN-конфиги
RUN mkdir -p /etc/openvpn/configs

# Создаём виртуальное окружение на базе Python 3.11
RUN python3.11 -m venv /opt/venv

# Активируем виртуальное окружение
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/requirements.txt

# Копируем скрипты внутрь контейнера
COPY entrypoint.sh /app/entrypoint.sh
COPY get_vpn_configs.py /app/get_vpn_configs.py
COPY connect_vpn.sh   /app/connect_vpn.sh
COPY get_product_links.py /app/get_product_links.py
COPY db_config.py /app/db_config.py

# Обновляем pip и устанавливаем Python-зависимости
RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt

# Даём права на выполнение скрипта подключения
RUN chmod +x /app/connect_vpn.sh /app/entrypoint.sh

# Устанавливаем рабочую директорию
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
