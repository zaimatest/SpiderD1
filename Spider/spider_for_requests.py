# spider_for_requests.py
# 可手动执行
import re
import time
from bs4 import BeautifulSoup
from curl_cffi import requests
from urllib.parse import urljoin  # 拼接url用

from tool.cherk_redirect import get_current_domain
from tool.parse import extract_books_and_pages
from tool.search import search
from ujson import load_json
from save_data import save_data
from setting import DOMAIN_NAME, TEXT_JSON_PATH, AD_LIST_PATH, FONTDICT_PATH

from loguru import logger

sort_No = 0  # 排序用

# 首页
INDEX_FRIST_URL = ""
# 主域名
this_DOMAIN_NAME = ""
FontDict = {}

# 全局 session
gl_session = None


def gl_init(userAgent):
    global gl_session
    gl_session = requests.Session()
    # headers = {'User-Agent': userAgent}
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': this_DOMAIN_NAME,
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        # 'referer': 'https://www.banzhu11111.com/12/12510/?__cf_chl_tk=7uzmlWQPxjelInZQhq4V7i.WCNcbBw7mc47vn2pAnng-1735539827-1.0.1.1-1lwdhn6RifuBsYtzmvhtXZ_tBOM6J_8M62nydZmpWFs',
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
        'user-agent': userAgent,
        # 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 Edg/131.0.0.0'
    }
    gl_session.headers.update(headers)
    # for cookie in Cookies:
    #     gl_session.cookies.set(cookie['name'], cookie['value'])


# 获取广告屏蔽列表
def get_ad_list():
    BAN_TEXT_LIST = []
    with open(AD_LIST_PATH, 'r', encoding='UTF-8') as f:
        for ban in f.read().split('\n'):
            BAN_TEXT_LIST.append(ban)
    logger.info('屏蔽列表获取成功')
    return BAN_TEXT_LIST


# 通用爬取方法
def scrape_page(url):
    global session
    logger.info(f'scraping {url}', )
    try:
        response = gl_session.get(url)
        return response.text
    except:
        logger.error(f'error occurred while scraping {url}')


def scrape_index(url):  # 爬取列表页
    return scrape_page(url)


def parse_index_Get_PAGE(HTML):  # 在第一次爬取详情页时，获取其总页数
    try:
        Soup = BeautifulSoup(HTML, 'lxml')
        PAGE_TEXT = list(Soup.select('.pagelistbox .page'))[0]
        PAGE_TEXT = PAGE_TEXT.get_text()
        PAGE_TEXT = re.search('(\d+)页', PAGE_TEXT, re.S).group().replace('页', '')
        PAGE = int(PAGE_TEXT)
        BOOKNAME = Soup.select('.right h1')[0].string
    except Exception as e:
        logger.error(e)
        logger.error(HTML)
        return None, None

    try:
        PAGE = int(PAGE_TEXT)
        return PAGE, BOOKNAME
    except:
        return None, None


def parse_index(HTML):  # 解析列表页
    Soup = BeautifulSoup(HTML, 'lxml')
    DETAIL_TEXTs = Soup.select('.chapter-list')
    DETAIL_url_List = []
    for DETAIL_TEXT in DETAIL_TEXTs:
        if DETAIL_TEXT.find("h4").string.find("最新章节") > 0:
            continue
        else:
            for DETAIL_url in DETAIL_TEXT.select('ul.list li a'):
                DETAIL_url_List.append(urljoin(this_DOMAIN_NAME, DETAIL_url.attrs["href"]))
    return DETAIL_url_List


def scrape_detail(url):
    return scrape_page(url)


def parse_detail(DETAIL_HTML, detail_url, ad_list=[]):  # √
    Soup = BeautifulSoup(DETAIL_HTML, 'lxml')
    Title = Soup.find(class_='container').h1.string
    # 24-12-30 div.neirong 节点换成 page-content 了
    # 直接爬div.neirong节点
    AText = str(Soup.find(class_='page-content'))

    Detail_urls = []
    Post_url = detail_url  # post获取剩余请求的URL
    PAGE_LIST = Soup.select('center.chapterPages a')
    if len(PAGE_LIST) == 0:
        PAGE_No = 1
        curr_No = 1
    else:
        curr_No = Soup.find(class_='curr').string.replace('【', '').replace('】', '')
        PAGE_No = len(PAGE_LIST)

        # 把获取剩余页面链接放在这里，以方便获取第四页链接进行Post
        for PAGE in range(2, PAGE_No + 1):
            detail_url = re.search(INDEX_FRIST_URL + '(/\d+)+', detail_url, re.S).group()
            Detail_url = detail_url + f'_{PAGE}.html'
            if PAGE == 4:
                Post_url = Detail_url
            Detail_urls.append(Detail_url)

        # 23.4.9 更新，它换了第二页的加密方法，换成AES加密了，这里不再适用。
        # 反而第五页却用到了 sojson5加密，因此对第五页启用sojson5反混淆

        # 24.12.30 更新，因为上了5S盾，所以所有的反爬措施，全部下了，乐
        # 目前只有第二页是AES加密的，因此只对第二页进行AES解密以节省资源
        # if curr_No == '2':
        #     if check_NeedDecipher(DETAIL_HTML):
        #         # print(DETAIL_HTML)
        #         secret_Data = re.search('secret\((\s*)\"(.*?)\"', DETAIL_HTML, re.S).group().replace('secret(',
        #                                                                                              '').replace('	',
        #                                                                                                          '').replace(
        #             '\n', '')
        #
        #         secret_str = re.search('secret\((\s*)\"(.*?)\",(\s*)\'(.*?)\',', DETAIL_HTML, re.S).group().replace(
        #             'secret(', '').replace('	', '').replace('\n', '')
        #
        #         secret_pw = re.search('\'(.*)\'', secret_str, re.S).group()
        #
        #         # 第二页解密出来的文本不带img图片也不带div节点，直接在解密后清洗数据
        #         AText = get_true_HTML_AES(secret_Data, secret_pw, ad_list)

        # # 目前只有第三页用到css自定义字体反爬，因此只对第三页做字体替换以节省资源
        # if curr_No == '3':
        #     ADETAIL_HTML = DETAIL_HTML[:]
        #     for AFontID, AWord in FontDict.items():
        #         ADETAIL_HTML = re.sub(AFontID, AWord, ADETAIL_HTML)
        #     AText = re.search('<div class="neirong">(\s*)(.*)?', ADETAIL_HTML).group()
        #     AText = re.sub('<div class="neirong">(\s*)', '', AText)
        #     AText = re.sub('</div>', '', AText)
        #     AText = re.sub('<div class=(.*)\sid="(.*?)">', '', AText)[1:]

        # # 第四页源码是不全的，剩余的部分会用一个Ajax请求获取
        # if curr_No == '4':
        #     if len(re.findall('\(\'.neirong\'\)\.append', DETAIL_HTML)) > 0:
        #         LastRespons = gl_session.post(Post_url, data={"j": "1"})
        #         if LastRespons.status_code == 200:
        #             AText = AText + LastRespons.text

        # # 目前只有第五页是乱序的，因此只对第五页进行排序以节省资源
        # if curr_No == '5':
        #     if check_NeedSort(AText):
        #         ns = re.search('var ns=\'(.*?)\'', DETAIL_HTML, re.S).group().replace('var ns=\'', '').replace('\'', '')
        #         AText = get_true_HTML(AText, ns)  # '''

    data = {'链接': detail_url,
            '名字': Title,
            '正文': AText[:50] + '...',
            '全文': AText,
            '本章节页数': PAGE_No,
            '当前页数': curr_No,
            'urls': Detail_urls
            }

    return data


def after_scrape_index(BOOKNAME, HTML, img_json, ad_list):  # 把爬取完列表页后需要做的操作放到这里
    global sort_No  # 排序用
    detail_urls = parse_index(HTML)  # 解析列表页，获取url
    for detail_url in detail_urls:
        # 这里补上主域名
        if this_DOMAIN_NAME not in detail_url:
            detail_url = "https://" + this_DOMAIN_NAME[:-1] + detail_url
        logger.info(f'scrape detail_url {detail_url}', )
        DETAIL_HTML = scrape_detail(detail_url)
        # 解析详情页，返回一个包含详情页内容的列表
        detail_data = parse_detail(DETAIL_HTML, detail_url, ad_list)

        Detail_url_continues = detail_data.get('urls')  # 剩余url列表
        page_continues = detail_data.get('本章节页数')  # 本章总页数
        curr_No = detail_data.get('当前页数')  #
        page_name = detail_data.get('名字')  #

        save_data(detail_data, BOOKNAME, addway='w', sort_No=sort_No,
                  img_json=img_json,
                  ad_list=ad_list)

        if page_continues > 1:  # 爬完详情页，先检测页数，如果多页，爬完它
            for Detail_url_continue in Detail_url_continues:
                DETAIL_HTML = scrape_detail(Detail_url_continue)  # INDEX_FRIST_URL + '/'+ Detail_url
                detail_data = parse_detail(DETAIL_HTML, detail_url, ad_list)
                # logger.info('detail data %s', detail_data)
                save_data(detail_data, BOOKNAME, addway='a', sort_No=sort_No,
                          img_json=img_json,
                          ad_list=ad_list)

        sort_No = sort_No + 1  # 排序字段+1


class SpReque():
    def __init__(self, INDEX_FRIST_URL):
        self.INDEX_FRIST_URL = INDEX_FRIST_URL

    def Spider_Book(self):
        img_json = load_json(TEXT_JSON_PATH)  # 获取图片对应文本字典
        ad_list = get_ad_list()
        HTML = scrape_index(self.INDEX_FRIST_URL + '/')  # 先爬首页拿页码
        Page, BOOKNAME = parse_index_Get_PAGE(HTML)  # 提取页数
        after_scrape_index(BOOKNAME, HTML, img_json, ad_list)  # 执行下一步分析操作
        for INDEX_Page in range(2, Page + 1):  # 第一页分析完毕，这里开始执行第二页。
            HTML = scrape_index(self.INDEX_FRIST_URL + f'_{INDEX_Page}/')
            after_scrape_index(BOOKNAME, HTML, img_json, ad_list)  # 执行下一步分析操作


def run(name):
    global INDEX_FRIST_URL
    global this_DOMAIN_NAME
    global FontDict
    FontDict = load_json(FONTDICT_PATH)
    this_DOMAIN_NAME = DOMAIN_NAME
    INDEX_FRIST_URL = urljoin(DOMAIN_NAME, this_DOMAIN_NAME)

    # # 采用自动化进行获取url和主域名
    # _dict = get_cookies_dict(name, DOMAIN_NAME)
    # logger.info(":: 获取的内容 》》》====================================================================================")
    # logger.info(_dict)
    # logger.info(":: ==================================================================================================")
    # if _dict['DOMAIN_NAME'] != DOMAIN_NAME:  # 检查是否域名被重定向
    #     this_DOMAIN_NAME = _dict['DOMAIN_NAME']
    # # 采用自动化进行获取url和主域名

    c_html = search(name, "./conf/config.ini", "./.env")
    _data = extract_books_and_pages(c_html)
    _dict = {}
    if _data["books"]:
        current_domain = get_current_domain("./conf/config.ini", "./.env")
        _dict = {'Booklen': _data["books"][0]["words"],
                 'BookName': _data["books"][0]['book_name'],
                 'Bookurl': current_domain + _data["books"][0]['book_url'],
                 'Cookies': None,
                 'userAgent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Mobile Safari/537.36',
                 'DOMAIN_NAME': f'{current_domain}/'}

    logger.info(":: 获取的内容 》》》====================================================================================")
    logger.info(_dict)
    logger.info(":: ==================================================================================================")

    if _dict['Bookurl'] == "":
        return "搜索无结果或未搜索词长度小于3"
    # gl_init(_dict["Cookies"], _dict["userAgent"])  # 4.9更新，要传入请求头中的ua
    gl_init(_dict["userAgent"])  # 无需传入cookies，仅使用ua即可
    INDEX_FRIST_URL = _dict["Bookurl"]
    INDEX_FRIST_URL = INDEX_FRIST_URL[:len(INDEX_FRIST_URL) - 1]
    Sp = SpReque(INDEX_FRIST_URL)
    Sp.Spider_Book()
    return "已完成"


def main():
    run('何谓正邪')  # 测试爬取的书籍


if __name__ == '__main__':
    start = time.time()
    main()
    logger.info(f'爬取完成，耗时：{str(time.time() - start)}秒', )
    # 边爬边洗，耗时 90.85329127311707
