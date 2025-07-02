#!/bin/bash

VPN_DIR="/etc/openvpn/configs"
LOG_FILE="/tmp/openvpn_test.log"
SUCCESS_FLAG="/tmp/openvpn_success.flag"

# Удаляем флаг и старые логи
rm -f "$LOG_FILE" "$SUCCESS_FLAG"

# Функция для проверки успешного подключения
check_connected() {
    # Подключено, если есть IP через tun0 или другой интерфейс VPN
    ip a | grep -q "tun0" && return 0
    return 1
}

# Перебираем все .ovpn файлы
for config in "$VPN_DIR"/*.ovpn; do
    echo "Пробуем $config..."

    # Запускаем OpenVPN в фоне
    openvpn --config "$config" --daemon --log "$LOG_FILE"

    # Ждем подключения (например, 15 секунд)
    for i in {1..15}; do
        sleep 1
        if check_connected; then
            echo "Успешно подключено через $config"
            touch "$SUCCESS_FLAG"
            break
        fi
    done

    # Если успех — выходим
    if [ -f "$SUCCESS_FLAG" ]; then
        break
    else
        echo "Не удалось подключиться через $config. Пробуем следующий."
        pkill -f "openvpn --config $config"
        sleep 2
    fi
done

# Проверка финального результата
if [ -f "$SUCCESS_FLAG" ]; then
    echo "VPN подключён успешно."
    exit 0
else
    echo "Не удалось подключиться ни по одному из конфигов."
    exit 1
fi
