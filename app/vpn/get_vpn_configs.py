import requests
import re

HEADERS = {
    'Accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }

MAIN_LINK = "https://vpnobratno.info/russia_server_list.html"

main_page=requests.get(MAIN_LINK, headers=HEADERS, verify=False, timeout=10).text

pattern_main = r'href=\"([^\"]+)\"[^>]*>TCP'

matches = re.findall(pattern_main, main_page)

for link in matches:
    response = requests.get(link)
    id = re.search(r"download_id=(\d*)", link).group(1)
    filename = id+'.ovpn'
    with open("/etc/openvpn/configs/"+filename, "wb") as f:
        f.write(response.content)     