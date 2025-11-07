import os
import requests
# from curl_cffi import requests
from urllib.parse import urlparse
import configparser

# CONFIG_PATH = "../conf/config.ini"
# ENV_PATH = "../.env"

def load_default_from_env(env_path: str) -> str:
    """
    从 .env 文件中加载默认域名
    """
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"未找到 {env_path} 文件，请创建并设置 DEFAULT_DOMAIN")

    default_domain = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith("DEFAULT_DOMAIN="):
                    default_domain = line.split("=", 1)[1].strip()
                    break

    if not default_domain:
        raise ValueError(f"{env_path} 中缺少 DEFAULT_DOMAIN 配置")
    return default_domain


def get_current_domain(config_path: str, env_path: str) -> str:
    """
    获取当前域名：
    1. 优先使用 config.ini 中已保存的域名
    2. 否则使用 .env 中的默认域名
    """
    config = configparser.ConfigParser()

    if os.path.exists(config_path):
        config.read(config_path, encoding="utf-8")
        if config.has_section("redirect") and config.has_option("redirect", "latest_domain"):
            return config.get("redirect", "latest_domain")

    # 如果config不存在或没有值，则使用env默认值
    return load_default_from_env(env_path)


def get_redirect_domain(url: str, timeout: int = 180) -> str:
    """
    检查URL是否重定向，如果有重定向则返回最终跳转后的域名
    """
    try:
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': url,
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': f'{url}/s.php',
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
        }
        response = requests.get(url, headers= headers, allow_redirects=True, timeout=timeout)
        final_url = response.url
        print("当前cookies为：")
        print(response.cookies)
        print("==========================================================")
        print("当前页面为：")
        print(response.text)
        print("==========================================================")
        return urlparse(final_url).netloc
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return url


def save_latest_domain(final_domain: str, config_path: str):
    """
    将最新的重定向域名保存到 config.ini 的 [redirect] 区域
    """
    config = configparser.ConfigParser()

    # 保留其他配置
    if os.path.exists(config_path):
        config.read(config_path, encoding="utf-8")

    if "redirect" not in config:
        config["redirect"] = {}

    config["redirect"]["latest_domain"] = final_domain

    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)

    print(f"已将最新域名 {final_domain} 保存到 {config_path}")


def updata_domain(_config_path="../conf/config.ini", _env_path="../.env"):
    # Step 1: 获取当前域名
    current_domain = get_current_domain(_config_path, _env_path)
    print(f"当前域名: {current_domain}")

    # Step 2: 检测是否有重定向
    url_to_check = f"https://{current_domain}"  # 假设使用域名拼接URL
    latest_domain = get_redirect_domain(url_to_check)

    # Step 3: 保存更新后的域名
    if latest_domain:
        save_latest_domain(latest_domain, _config_path)
    else:
        print("未能获取重定向域名，保留当前配置。")


if __name__ == "__main__":
    updata_domain()