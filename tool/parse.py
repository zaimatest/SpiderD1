from bs4 import BeautifulSoup
import json
import re


def extract_books_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    result = []

    # 定位到书籍列表
    ul = soup.select_one('div.mod.block.book-all-list div.bd ul')
    if not ul:
        print("未找到书籍列表")
        return result

    for li in ul.select('li.column-2'):
        item = {}

        # 书名及链接
        name_tag = li.select_one('a.name')
        if name_tag:
            item['book_name'] = name_tag.get_text(strip=True)
            item['book_url'] = name_tag['href']

        # 最新章节
        update_tag = li.select_one('p.update a')
        if update_tag:
            item['latest_chapter'] = update_tag.get_text(strip=True)
            item['latest_chapter_url'] = update_tag['href']

        # 作者
        info_tag = li.select_one('p.info')
        if info_tag:
            text = info_tag.get_text(" ", strip=True)
            # 通常格式：作者：XXX 字数：YYYY
            if '作者：' in text:
                author_part = text.split('作者：')[1]
                if '字数：' in author_part:
                    author, words = author_part.split('字数：', 1)
                    item['author'] = author.strip()
                    item['words'] = words.strip()
                else:
                    item['author'] = author_part.strip()
                    item['words'] = ''

        result.append(item)

    return result


def extract_books_and_pages(html):
    soup = BeautifulSoup(html, 'html.parser')

    result = []
    total_pages = None

    # ── ① 提取书籍列表 ────────────────────────────────
    ul = soup.select_one('div.mod.block.book-all-list div.bd ul')
    if ul:
        for li in ul.select('li.column-2'):
            item = {}

            # 书名及链接
            name_tag = li.select_one('a.name')
            if name_tag:
                item['book_name'] = name_tag.get_text(strip=True)
                item['book_url'] = name_tag['href']

            # 最新章节
            update_tag = li.select_one('p.update a')
            if update_tag:
                item['latest_chapter'] = update_tag.get_text(strip=True)
                item['latest_chapter_url'] = update_tag['href']

            # 作者 + 字数
            info_tag = li.select_one('p.info')
            if info_tag:
                text = info_tag.get_text(" ", strip=True)
                # 通常格式：作者：XXX 字数：YYYY
                if '作者：' in text:
                    author_part = text.split('作者：')[1]
                    if '字数：' in author_part:
                        author, words = author_part.split('字数：', 1)
                        item['author'] = author.strip()
                        item['words'] = words.strip()
                    else:
                        item['author'] = author_part.strip()
                        item['words'] = ''

            result.append(item)

    # ── ② 提取总页数 ────────────────────────────────
    page_box = soup.select_one('div.pagelistbox')
    if page_box:
        text = page_box.get_text(" ", strip=True)
        # 匹配 “第1/2页” 中的 “2”
        match = re.search(r'第\d+\/(\d+)页', text)
        if match:
            total_pages = int(match.group(1))

    return {
        "books": result,
        "total_pages": total_pages
    }

if __name__ == '__main__':
    # # 读取本地 html 文件内容
    # with open('./temp/搜索结果.HTML', 'r', encoding='utf-8') as f:
    #     html_content = f.read()
    #
    # books = extract_books_from_html(html_content)
    #
    # # 打印结果
    # print(json.dumps(books, indent=2, ensure_ascii=False))

    # 从本地 HTML 文件读取
    with open('../temp/搜索结果.HTML', 'r', encoding='utf-8') as f:
        html_content = f.read()

    data = extract_books_and_pages(html_content)

    print(json.dumps(data, indent=2, ensure_ascii=False))