import os
import subprocess
import time
import glob
from pathlib import Path


VPN_DIR = "/etc/openvpn/configs"
LOG_FILE = "/tmp/openvpn_test.log"
SUCCESS_FLAG = "/tmp/openvpn_success.flag"
DB_IP = os.getenv("DB_HOST", "")

def log(msg):
    with open(LOG_FILE, "a") as f:
        print(msg)
        f.write(msg + "\n")

def get_original_gateway():
    result = subprocess.run(["ip", "route"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("default") and "tun0" not in line:
            return line.split()[2]
    return None

def check_connected():
    result = subprocess.run(["ip", "a"], capture_output=True, text=True)
    return "tun0" in result.stdout

def add_route_to_db(db_ip, via_gw):
    if db_ip and via_gw:
        subprocess.run(["ip", "route", "add", db_ip, "via", via_gw])

def update_dns():
    with open("/etc/resolv.conf", "w") as f:
        f.write("nameserver 8.8.8.8\n")
        f.write("nameserver 1.1.1.1\n")

def kill_openvpn(config):
    subprocess.run(["pkill", "-f", f"openvpn --config {config}"])

def main():
    log("=== [VPN] Запуск VPN подключения ===")
    orig_gw = get_original_gateway()
    log(f"Исходный шлюз локальной сети: {orig_gw}")

    for config in glob.glob(os.path.join(VPN_DIR, "*.ovpn")):
        log(f"Пробуем {config}...")

        subprocess.Popen(["openvpn", "--config", config, "--daemon", "--log", LOG_FILE])

        for i in range(15):
            time.sleep(1)
            if check_connected():
                log(f"Успешно подключено через {config}")
                Path(SUCCESS_FLAG).touch()
                add_route_to_db(DB_IP, orig_gw)
                update_dns()
                log("VPN подключён, маршруты и DNS настроены.")
                return 0

        log(f"Не удалось подключиться через {config}")
        kill_openvpn(config)
        time.sleep(2)

    log("Не удалось подключиться ни по одному из конфигов.")
    return 1

if __name__ == "__main__":
    exit(main())
