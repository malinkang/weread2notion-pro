import argparse
import os

import pendulum
import requests
from notion_helper import NotionHelper

from weread_api import WeReadApi
import utils
from config import (
    book_properties_type_dict,
)
from retrying import retry

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"

rating = {"poor": "⭐️ 不看", "fair": "⭐️⭐️ 一般", "good": "⭐️⭐️⭐️ 推荐"}


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def get_douban_url(isbn):
    print(f"get_douban_url {isbn} ")
    params = {"query": isbn, "page": "1", "category": "book"}
    r = requests.get("https://neodb.social/api/catalog/search", params=params)
    books = r.json().get("data")
    if books is None or len(books) == 0:
        return None
    results = list(filter(lambda x: x.get("isbn") == isbn, books))
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


def insert_book_to_notion(books, index, bookId):
    """插入Book到Notion"""
    book = {}
    if bookId in archive_dict:
        book["书架分类"] = archive_dict.get(bookId)
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
    if cover.startswith("http"):
        if not cover.endswith(".jpg"):
            cover = utils.upload_cover(cover)
        else:
            cover = cover.replace("/s_", "/t7_")
    else:
        cover = BOOK_ICON_URL
    isbn = book.get("isbn")
    if isbn and isbn.strip():
        douban_url = get_douban_url(isbn)
        if douban_url:
            book["douban_url"] = douban_url
    book["图书封面"] = cover
    book["阅读进度"] = (
        100 if (book.get("markedStatus") == 4) else book.get("readingProgress", 0)
    ) / 100
    markedStatus = book.get("markedStatus")
    status = "想读"
    if markedStatus == 4:
        status = "速读⏰"
    elif markedStatus == 3:
        status = "弃读📕"
    elif book.get("readingTime", 0) >= 60:
        status = "初读📗"
    book["阅读状态"] = status
    book["微读时长"] = book.get("readingTime")
    book["阅读天数"] = book.get("totalReadDay")
    book["大众评分"] = int(book.get("newRating"))/1000
    if book.get("newRatingDetail") and book.get("newRatingDetail").get("myRating"):
        book["个人评级"] = rating.get(book.get("newRatingDetail").get("myRating"))
    elif status== "弃读📕":
        book["个人评级"] = "⭐️ 不看"
    elif status== "速读⏰":
        book["个人评级"] = "⭐️⭐️ 一般"
    date = None
    if book.get("finishedDate"):
        date = book.get("finishedDate")
    elif book.get("lastReadingDate"):
        date = book.get("lastReadingDate")
    elif book.get("readingBookDate"):
        date = book.get("readingBookDate")
    elif book.get("beginReadingDate"):
        date = book.get("beginReadingDate")
    book["时间"] = date
        
    if book.get("beginReadingDate"):
        book["阅读时间"] = [book.get("beginReadingDate"), date]
    else:
        book["阅读时间"] = [date, date]
    if bookId not in notion_books:
        book["图书名称"] = book.get("title")
        try:
            book["出版机构"] = book.get("publisher").replace(",", " ").replace(".", " ")
        except:
            book["出版机构"] = "未知"
                
        book["图书 ID"] = book.get("bookId")
        book["ISBN"] = book.get("isbn")
        book["微读链接"] = utils.get_weread_url(bookId)
        book["内容简介"] = book.get("intro")
        book["作者"] = [
            notion_helper.get_relation_id(
                x, notion_helper.author_database_id, USER_ICON_URL
            )
            for x in book.get("author").split(" ")
        ]
        if book.get("categories"):
            book["微读分类"] = [
                notion_helper.get_relation_id(
                    x.get("title"), notion_helper.category_database_id, TAG_ICON_URL
                )
                for x in book.get("categories")
            ]
    properties = utils.get_properties(book, book_properties_type_dict)
    if properties["阅读时间"]["date"]["start"] == None:
        properties["阅读时间"]["date"] = None
    if book.get("时间"):
        notion_helper.get_date_relation(
            properties,
            pendulum.from_timestamp(book.get("时间"), tz="Asia/Shanghai"),
        )

    print(f"正在插入《{book.get('title')}》,一共{len(books)}本，当前是第{index+1}本。")
    parent = {"database_id": notion_helper.book_database_id, "type": "database_id"}
    if bookId in notion_books:
        notion_helper.update_page(
            page_id=notion_books.get(bookId).get("pageId"),
            properties=properties,
            icon=utils.get_icon(book.get("图书封面")),
        )
    else:
        notion_helper.create_page(
            parent=parent,
            properties=properties,
            icon=utils.get_icon(book.get("图书封面")),
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
            (
                key not in bookProgress
                or value.get("readingTime") == bookProgress.get(key).get("readingTime")
            )
            and (archive_dict.get(key) == value.get("category"))
            and value.get("cover")
            and (not value.get("cover").endswith("/0.jpg"))
            and (not value.get("cover").endswith("parsecover"))
            and (
                value.get("status") != "已读"
                or (value.get("status") == "已读" and value.get("myRating"))
            )
            or (value.get("archive") is True)
        ):
            not_need_sync.append(key)
    notebooks = weread_api.get_notebooklist()
    notebooks = [d["bookId"] for d in notebooks if "bookId" in d]
    books = bookshelf_books.get("books")
    books = [d["bookId"] for d in books if "bookId" in d]
    books = list((set(notebooks) | set(books)) - set(not_need_sync))
    for index, bookId in enumerate(books):
        insert_book_to_notion(books, index, bookId)
