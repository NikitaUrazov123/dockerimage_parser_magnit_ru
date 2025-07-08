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

WORKDIR /app

COPY app/ /app/


RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt


ENTRYPOINT ["python3", "-m", "main"]