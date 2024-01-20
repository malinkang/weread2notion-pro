import argparse
import hashlib
import json
import os

import pendulum
import requests
from notion_helper import NotionHelper

from weread_api import WeReadApi
import utils
from config import (
    book_properties_name_dict,
    book_properties_type_dict,
)
from bs4 import BeautifulSoup
from retrying import retry

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def get_douban_url(title, isbn):
    """
    不知道怎么直接根据isbn获取douban的链接
    直接曲线通过NeoDB来获取，But NeoDB有点数据不全
    不一定能搜索到，而且通过名字搜索出来的书可能不对
    """
    query = isbn if isbn and isbn.strip() else title
    print(f"search_neodb {title} {isbn} ")
    params = {"query": query, "page": "1", "category": "book"}
    print(query)
    r = requests.get("https://neodb.social/api/catalog/search", params=params)
    books = r.json().get("data")
    if books is None or len(books) == 0:
        return None
    results = list(filter(lambda x: x.get("isbn") == query, books))
    if len(results) == 0:
        results = list(filter(lambda x: x.get("display_title") == query, books))
    if len(results) == 0:
        return None
    result = results[0]
    urls = list(
        filter(
            lambda x: x.get("url").startswith("https://book.douban.com"),
            result.get("external_resources", []),
        )
    )
    if len(urls) == 0:
        return None
    return urls[0].get("url")


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def douban_book_parse(link):
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.content)
    result = {}
    result["title"] = soup.find(property="v:itemreviewed").string
    result["cover"] = soup.find(id="mainpic").img["src"]
    authors = soup.find_all("li", class_="author")
    authors = [
        author.find("a", class_="name").string
        for author in authors
        if author.find("a", class_="name") is not None
    ]
    result["author"] = authors
    info = soup.find(id="info")
    info = list(map(lambda x: x.replace(":", "").strip(), info.stripped_strings))
    if "ISBN" in info:
        result["isbn"] = info[info.index("ISBN") + 1 :][0]
    return result


def insert_book_to_notion(books, index, bookId):
    """插入Book到Notion"""
    book = {}
    if bookId in archive_dict:
        book["archive"] = archive_dict.get(bookId)
    if bookId in notion_books:
        book.update(notion_books.get(bookId))
    bookInfo = weread_api.get_bookinfo(bookId)
    if bookInfo != None:
        book.update(bookInfo)
    readInfo = weread_api.get_read_info(bookId)
    # 研究了下这个状态不知道什么情况有的虽然读了状态还是1 markedStatus = 1 想读 4 读完 其他为在读
    readInfo.update(readInfo.get("readDetail", {}))
    readInfo.update(readInfo.get("bookInfo", {}))
    book.update(readInfo)
    cover = book.get("cover")
    author = book.get("author")
    if author == "公众号":
        if not cover.startswith("http"):
            book["cover"] = BOOK_ICON_URL
        if cover.startswith("http") and not cover.endswith(".jpg"):
            book["cover"] = f"{cover}.jpg"
        book["author"] = ["公众号"]
    douban_url = book.get("douban_url")
    """不是公众号并且douban链接为None"""
    if author != "公众号" and (not douban_url or not douban_url.strip()):
        douban_url = get_douban_url(book.get("title"), book.get("isbn"))
    douban_book = None
    if douban_url:
        douban_book = douban_book_parse(douban_url)
    if douban_book:
        """获取的ISBN未必正确所以优先判断有ISBN没没有再从豆瓣拿"""
        isbn = book.get("isbn")
        book["douban_url"] = douban_url
        if not isbn or not isbn.strip():
            book["isbn"] = douban_book.get("isbn")
        """微信读书的作者名有点恶心，从豆瓣取了"""
        book["author"] = douban_book.get("author")
        """自己传的书获取的封面Notion不能展示用douban的封面吧"""
        if cover.startswith("http") and not cover.endswith(".jpg"):
            book["cover"] = douban_book.get("cover")
        else:
            """替换为高清图"""
            book["cover"] = book.get("cover").replace("/s_", "/t7_")
    elif author != "公众号":
        book["author"] = book.get("author").split(" ")
        """替换为高清图"""
        book["cover"] = book.get("cover").replace("/s_", "/t7_")
    book["readingProgress"] = (
        100 if (book.get("markedStatus") == 4) else book.get("readingProgress", 0)
    ) / 100
    status = {1: "想读", 4: "已读"}
    book["status"] = status.get(book.get("markedStatus"), "在读")
    date = None
    if book.get("finishedDate"):
        date = book.get("finishedDate")
    elif book.get("lastReadingDate"):
        date = book.get("lastReadingDate")
    elif book.get("readingBookDate"):
        date = book.get("readingBookDate")
    book["date"] = date
    book["author"] = [
        notion_helper.get_relation_id(
            x, notion_helper.author_database_id, USER_ICON_URL
        )
        for x in book.get("author")
    ]
    book["url"] = utils.get_weread_url(bookId)
    if book.get("categories"):
        book["categories"] = [
            notion_helper.get_relation_id(
                x.get("title"), notion_helper.category_database_id, TAG_ICON_URL
            )
            for x in book.get("categories")
        ]
    properties = utils.get_properties(
        book, book_properties_name_dict, book_properties_type_dict
    )
    if book.get("date"):
        notion_helper.get_date_relation(
            properties,
            pendulum.from_timestamp(book.get("date"), tz="Asia/Shanghai"),
        )
    print(f"正在插入《{book.get('title')}》,一共{len(books)}本，当前是第{index+1}本。")
    parent = {"database_id": notion_helper.book_database_id, "type": "database_id"}
    if bookId in notion_books:
        notion_helper.update_page(
            page_id=notion_books.get(bookId).get("pageId"),
            properties=properties,
            icon=utils.get_icon(book.get("cover")),
        )
    else:
        notion_helper.create_page(
            parent=parent,
            properties=properties,
            icon=utils.get_icon(book.get("cover")),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    options = parser.parse_args()
    weread_cookie = os.getenv("WEREAD_COOKIE")
    branch = os.getenv("REF").split("/")[-1]
    repository = os.getenv("REPOSITORY")
    weread_api = WeReadApi()
    notion_helper = NotionHelper()
    notion_books = notion_helper.get_all_book()
    bookshelf_books = weread_api.get_bookshelf()
    bookProgress = bookshelf_books.get("bookProgress")
    bookProgress = {book.get("bookId"): book for book in bookProgress}
    archive_dict = {}
    for archive in bookshelf_books.get("archive"):
        name = archive.get("name")
        bookIds = archive.get("bookIds")
        archive_dict.update({bookId: name for bookId in bookIds})
    not_need_sync = []
    for key, value in notion_books.items():
        if (
            key not in bookProgress
            or value.get("readingTime") == bookProgress.get(key).get("readingTime")
        ) and archive_dict.get(key) == value.get("category"):
            not_need_sync.append(key)
    notebooks = weread_api.get_notebooklist()
    notebooks = [d["bookId"] for d in notebooks if "bookId" in d]
    books = bookshelf_books.get("books")
    books = [d["bookId"] for d in books if "bookId" in d]
    books = list((set(notebooks) | set(books)) - set(not_need_sync))
    for index, bookId in enumerate(books):
        insert_book_to_notion(books, index, bookId)
