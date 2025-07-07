#!/bin/bash

VPN_DIR="/etc/openvpn/configs"
LOG_FILE="/tmp/openvpn_test.log"
SUCCESS_FLAG="/tmp/openvpn_success.flag"
DB_IP="192.168.110.187"

echo "=== [VPN] Запуск VPN подключения ===" | tee -a "$LOG_FILE"

# Сохраняем исходный шлюз (для маршрута к БД)
ORIG_GW=$(ip route | awk '/^default/ && $0 !~ /tun0/ {print $3; exit}')
echo "Исходный шлюз локальной сети: $ORIG_GW" | tee -a "$LOG_FILE"

# Функция проверки подключения
check_connected() {
    ip a | grep -q "tun0" && return 0
    return 1
}

# Перебор конфигов
for config in "$VPN_DIR"/*.ovpn; do
    echo "Пробуем $config..." | tee -a "$LOG_FILE"

    openvpn --config "$config" --daemon --log "$LOG_FILE"

    # Ждём tun0
    for i in {1..15}; do
        sleep 1
        if check_connected; then
            echo "Успешно подключено через $config" | tee -a "$LOG_FILE"
            touch "$SUCCESS_FLAG"
            break
        fi
    done

    if [ -f "$SUCCESS_FLAG" ]; then
        # Добавляем маршрут к БД через локальный шлюз
        echo "Добавляю маршрут к БД ($DB_IP) через $ORIG_GW" | tee -a "$LOG_FILE"
        ip route add "$DB_IP" via "$ORIG_GW"
        # Публичные DNS
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 1.1.1.1" >> /etc/resolv.conf
        break
    else
        echo "Не удалось подключиться через $config" | tee -a "$LOG_FILE"
        pkill -f "openvpn --config $config"
        sleep 2
    fi
done


if [ -f "$SUCCESS_FLAG" ]; then
    echo "VPN подключён, маршруты и DNS настроены." | tee -a "$LOG_FILE"
    exit 0
else
    echo "Не удалось подключиться ни по одному из конфигов." | tee -a "$LOG_FILE"
    exit 1
fi
