# Переменные окружения:
# - DB_HOST        — адрес сервера PostgreSQL (например, 192.168.110.187)
# - DB_PORT        — порт PostgreSQL (например, 5432)
# - DB_NAME        — имя базы данных
# - DB_USER        — имя пользователя для подключения к БД (например, parser)
# - DB_PASSWORD    — пароль пользователя
#
# Необходимые флаги и параметры:
# --rm             — автоматически удалить контейнер после завершения работы
# -it              — интерактивный режим с TTY
# --cap-add=NET_ADMIN — добавление привелегий для работы с сетевыми интерфейсами
# --device /dev/net/tun — доступ к устройству /dev/net/tun (для VPN, tunneling и т.п.)
#
# Пример запуска:
# docker run --rm -it \
#   --cap-add=NET_ADMIN \
#   --device /dev/net/tun \
#   -e DB_HOST=192.168.110.187 \
#   -e DB_PORT=5432 \
#   -e DB_NAME=my_db \
#   -e DB_USER=parser \
#   -e DB_PASSWORD=my_password \
#   scraper_magnit_ru

FROM ubuntu:22.04

# Отключаем интерактивные диалоги у apt и задаём часовой пояс
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Minsk

# Добавляем PPA для Python 3.11
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update

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


RUN mkdir -p /etc/openvpn/configs

RUN python3.11 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY app/ /app/

RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt

ENTRYPOINT ["python3", "-m", "main"]