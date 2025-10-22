import os
import re
import hashlib
from PIL import Image
from loguru import logger
from ddddocr import DdddOcr
from curl_cffi import requests

import logging

from Spider.ujson import load_json, save_json

# 设置日志级别为 WARNING 或 ERROR，避免输出欢迎信息
logging.basicConfig(level=logging.ERROR)

this_DOMAIN_NAME = 'https://www.banzhu11111.com'

def remove_duplicates_from_txt(file_path):
    """
    从格式化好的txt文件中移除重复行，并重新保存。
    :param file_path: 要处理的txt文件路径
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 去重并保持顺序
        unique_lines = list(dict.fromkeys(line.strip() for line in lines if line.strip()))

        # 将去重后的内容写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(unique_lines) + '\n')

        logger.info("文件去重并保存成功！")
        return unique_lines
    except FileNotFoundError:
        logger.error(f"错误：文件 {file_path} 未找到！")
        return []
    except Exception as e:
        logger.error(f"发生错误：{e}")
        return []


def save_img_in_local(img_name = ""):
    if img_name != "":
        root_path = f"./img_tmp"
        if not os.path.exists(root_path):
            os.makedirs(root_path)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': this_DOMAIN_NAME,
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-arch': '""',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version': '"131.0.2903.86"',
            'sec-ch-ua-full-version-list': '"Microsoft Edge";v="131.0.2903.86", "Chromium";v="131.0.6778.109", "Not_A Brand";v="24.0.0.0"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-model': '"Nexus 5"',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-platform-version': '"6.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': "'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Mobile Safari/537.36'",
            # 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 Edg/131.0.0.0'
        }
        try:
            response = requests.get(f'{this_DOMAIN_NAME}/toimg/data/{img_name}', headers=headers)
            if response.status_code == 200:
                # 保存图片到本地
                with open(f'{root_path}/{img_name}', 'wb') as f:
                    f.write(response.content)
                logger.info(f"图片[{img_name}]已成功保存")
            else:
                logger.error(f"请求错误，response.status_code = {response.status_code}")
                logger.error(response.text)
        except Exception as e:
            logger.error(f"图片下载错误：{e}")
    else:
        logger.error(f"图片名不能为空")


def calculate_md5(image_path):
    # 创建一个 MD5 哈希对象
    md5_hash = hashlib.md5()

    # 打开图片文件并读取
    with open(image_path, "rb") as f:
        # 分块读取文件内容并更新哈希
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)

    # 返回最终的 MD5 值
    return md5_hash.hexdigest()


def get_new_text():
    # 1、去重
    file_path = 'uncheck_img.txt'
    unique_lines = remove_duplicates_from_txt(file_path)

    # # 2、获取去重后的列表，逐个下载图片并保存到本地
    # for img_name in unique_lines:
    #     save_img_in_local(img_name)

    text_json = load_json("../Spider/text.json")
    text_list = text_json["texts"]

    # 3、使用ocr识别出每一个图片中的文本
    for img_name in unique_lines:
        # 读取小图片
        img_path = f'./img_tmp/{img_name}'
        img = Image.open(img_path).convert("RGBA")

        # 放大图片
        scale_factor = 5  # 放大倍数
        large_img = img.resize(
            (img.width * scale_factor, img.height * scale_factor), Image.LANCZOS
        )

        # 转换透明背景为白色
        white_background = Image.new("RGBA", large_img.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(white_background, large_img)

        # 转为 RGB 格式
        rgb_img = composite.convert("RGB")

        # 嵌入更大的白色背景
        padding = 50  # 四周留白的像素宽度
        new_width = rgb_img.width + padding * 2
        new_height = rgb_img.height + padding * 2

        # 创建大背景
        large_background = Image.new("RGB", (new_width, new_height), (255, 255, 255))

        # 将放大的图片粘贴到背景中央
        offset = (padding, padding)
        large_background.paste(rgb_img, offset)

        # 保存处理后的图片
        new_img_path = './img_tmp/enlarged_and_embedded_image.png'
        large_background.save(new_img_path)

        # 使用 ddddocr 识别
        ocr = DdddOcr(show_ad=False)
        with open(new_img_path, 'rb') as f:
            img_bytes = f.read()
        text = ocr.classification(img_bytes)
        imgMD5 = calculate_md5(img_path)
        logger.info(f"{img_name} 的识别结果为: {text}，图片MD5:{imgMD5}")

        # 4、将结果作为字典保存在 ./Spider/text.json
        text_dict = {
            "imgName": img_name,
            "text": text,
            "md5": imgMD5
        }
        text_list.append(text_dict)

    save_json("../Spider/text.json", {"texts": text_list})


def replace_img(_book_path=""):
    logger.info(f"读取书本：{_book_path}")
    with open(_book_path, "r", encoding='utf-8') as bookf:
        book = bookf.read()
    text_json = load_json("../Spider/text.json")
    text_list = text_json["texts"]
    text_dict = {}  # 图片名 - 文本字典
    for _item in text_list:
        text_dict[_item.get("imgName")] = _item.get("text")

    pattern = r'<img data-cfsrc="[^"]*" style="[^"]*<noscript><img src="[^"]*</noscript>'
    # 查找所有匹配项
    matches = re.findall(pattern, book)
    # 输出结果
    img_ele_list = []
    for match in matches:
        img_ele_list.append(str(match))
    img_ele_list = list(set(img_ele_list))  # 需要替换的图片节点字符串列表
    for img_ele in img_ele_list:
        # logger.info(str(img_ele))
        pattern_t =  r'data/([^"]+\.png)'
        match = re.search(pattern_t, str(img_ele))
        if match:
            _text = text_dict.get(match.group().replace("data/", ""), str(img_ele))
            book = book.replace(str(img_ele), _text)
            logger.info(f"将节点：{str(img_ele)} 替换为：{_text}")
    logger.info(book[:200])
    with open(_book_path, "w", encoding='utf-8') as bookf:
        bookf.write(book)
        logger.info(f"将清洗后的书本保存回：{_book_path}")


def clear(_book_path=""):
    logger.info(f"读取书本：{_book_path}")
    with open(_book_path, "r", encoding='utf-8') as bookf:
        book = bookf.read()

    pattern = r'</p><!--baidu-->(.*?)</center>'
    # 查找所有匹配项
    matches = re.findall(pattern, book)
    # 输出结果
    img_ele_list = []
    for match in matches:
        img_ele_list.append(str(match))
    img_ele_list = list(set(img_ele_list))  # 需要替换的图片节点字符串列表
    for img_ele in img_ele_list:
        book = book.replace(str(img_ele), "")
        logger.info(f"将节点：{str(img_ele)} 替换为空")
    logger.info(book[:200])
    book = book.replace("<p>", "")
    book = book.replace("</p><!--baidu--></center>", "")
    with open(_book_path, "w", encoding='utf-8') as bookf:
        bookf.write(book)
        logger.info(f"将清洗后的书本保存回：{_book_path}")


def main(book_path):
    # 第一步，将所有新的url识别出来
    get_new_text()
    # 第二步，替换图片
    replace_img(book_path)
    # 第三步，清洗
    clear(book_path)


if __name__ == '__main__':
    main(book_path="../WriteBook/浊尘寻欢录.txt")

