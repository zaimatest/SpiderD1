import sys
from tool.cherk_redirect import updata_domain

sys.path.append('Spider')
from Spider.spider_for_requests import run as runSpider


def main():
    updata_domain("./conf/config.ini", "./.env")
    runSpider('浊尘寻欢录')  # 狩猎女格斗家


if __name__ == '__main__':
    # 不要挂梯子，挂梯子可能过不去cf
    main()
