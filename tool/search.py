import requests
import urllib.parse
from loguru import logger

from tool.cherk_redirect import get_current_domain
from tool.parse import extract_books_and_pages

# CONFIG_PATH = "../conf/config.ini"
# ENV_PATH = "../.env"

def encode_to_gbk_url(text: str) -> str:
    """
    将中文字符串按照 GBK 编码转换成 URL 编码格式
    例如：'疯了女歌手家' -> '%E1%F7%C1%D4%C5%AE%B8%F1%B6%B7%BC%D2'
    """
    return urllib.parse.quote(text, encoding='gbk')

def search(key_word, _config_path="../conf/config.ini", _env_path="../.env"):
    current_domain = get_current_domain(_config_path, _env_path)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.banzhu5555555.com',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://www.banzhu5555555.com/s.php',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        'sec-ch-ua-arch': '""',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"139.0.3405.111"',
        'sec-ch-ua-full-version-list': '"Not;A=Brand";v="99.0.0.0", "Microsoft Edge";v="139.0.3405.111", "Chromium";v="139.0.7258.139"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-model': '"Nexus 5"',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua-platform-version': '"6.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36 Edg/139.0.0.0',
        # 'cookie': 'cf_chl_rc_ni=1; Hm_lvt_d6f37f57aac98f699f260e668b6371b1=1759223445; Hm_lpvt_d6f37f57aac98f699f260e668b6371b1=1759223445; HMACCOUNT=B6C2047C2F8022A5; Hm_lvt_78f600208fff414fbaa01868606be1c0=1759223445; Hm_lpvt_78f600208fff414fbaa01868606be1c0=1759223445; Hm_tf_4wsjxav6hdj=1759223445; Hm_lvt_4wsjxav6hdj=1759223445; Hm_lpvt_4wsjxav6hdj=1759223445; PHPSESSID=6d77surrv70h5gikath9ug8n65',
    }
    data = f'objectType=2&type=articlename&s={encode_to_gbk_url(key_word)}'
    try:
        response = requests.post(f'https://{current_domain}/s.php', headers=headers, data=data)
        # print("==========================================================")
        logger.info(response.status_code)
        # print("==========================================================")
        logger.info(response.cookies)
        # print("==========================================================")
        # print(response.text)
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f":{response.text}")
            return ""
    except Exception as e:
        logger.error(f":{e}")
        return ""

if __name__ == '__main__':
    c_html = search("浊尘寻欢录")
    _data = extract_books_and_pages(c_html)
    current_domain = get_current_domain("../conf/config.ini", "../.env")
    if _data["books"]:
        _dict = {'Booklen': _data["books"][0]["words"],
                'BookName': _data["books"][0]['book_name'],
                'Bookurl': current_domain + _data["books"][0]['book_url'],
                'Cookies': None,
                'userAgent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Mobile Safari/537.36', 'DOMAIN_NAME': 'https://www.banzhu4444444.com/'}
    print(_dict)



