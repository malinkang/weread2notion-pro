import pendulum

from weread2notionpro import utils
from weread2notionpro.config import book_properties_type_dict, tz
from weread2notionpro.notion_helper import NotionHelper
from weread2notionpro.weread_api import WeReadApi

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"
rating = {"poor": "⭐️", "fair": "⭐️⭐️⭐️", "good": "⭐️⭐️⭐️⭐️⭐️"}


def insert_book_to_notion(books, index, bookId):
    """插入Book到Notion"""
    book = {}
    if bookId in archive_dict:
        book["书架分类"] = archive_dict.get(bookId)
    if bookId in notion_books:
        book.update(notion_books.get(bookId))

    # 尝试从 books_metadata 中获取基础信息（来自 entire_shelf）
    if bookId in books_metadata:
        book.update(books_metadata[bookId])

    try:
        bookInfo = weread_api.get_bookinfo(bookId)
        if bookInfo != None:
            book.update(bookInfo)
    except Exception as e:
        # 本地书籍（CB_ 开头）无法通过 API 获取详细信息，这是正常的
        if not bookId.startswith("CB_"):
            print(f"获取书籍信息失败 bookId={bookId}: {e}")

    try:
        readInfo = weread_api.get_read_info(bookId)
    except Exception as e:
        if not bookId.startswith("CB_"):
            print(f"获取阅读信息失败 bookId={bookId}: {e}")
        readInfo = {}
    # 研究了下这个状态不知道什么情况有的虽然读了状态还是1 markedStatus = 1 想读 4 读完 其他为在读
    if readInfo:
        readInfo.update(readInfo.get("readDetail", {}))
        readInfo.update(readInfo.get("bookInfo", {}))
        book.update(readInfo)
    # 处理可能为 None 的数值字段
    book["阅读进度"] = (
        100 if (book.get("markedStatus") == 4) else (book.get("readingProgress") or 0)
    ) / 100
    markedStatus = book.get("markedStatus")
    status = "想读"
    if markedStatus == 4:
        status = "已读"
    elif (book.get("readingTime") or 0) >= 60:
        status = "在读"
    book["阅读状态"] = status
    book["阅读时长"] = book.get("readingTime") or 0
    book["阅读天数"] = book.get("totalReadDay") or 0
    book["评分"] = book.get("newRating")
    if book.get("newRatingDetail") and book.get("newRatingDetail").get("myRating"):
        book["我的评分"] = rating.get(book.get("newRatingDetail").get("myRating"))
    elif status == "已读":
        book["我的评分"] = "未评分"
    book["时间"] = (
        book.get("finishedDate")
        or book.get("lastReadingDate")
        or book.get("readingBookDate")
    )
    book["开始阅读时间"] = book.get("beginReadingDate")
    book["最后阅读时间"] = book.get("lastReadingDate")
    cover = book.get("cover")
    # 如果cover是字符串，进行替换；如果是字典，提取URL
    if isinstance(cover, str):
        cover = cover.replace("/s_", "/t7_")
    elif isinstance(cover, dict):
        cover = cover.get("url", "") or cover.get("external", {}).get("url", "")
    else:
        cover = str(cover) if cover else ""

    if not cover or not cover.strip() or not cover.startswith("http"):
        cover = BOOK_ICON_URL
    if bookId not in notion_books:
        book["书名"] = book.get("title") or f"未知书名-{bookId}"
        book["BookId"] = book.get("bookId")
        book["ISBN"] = book.get("isbn")
        book["链接"] = weread_api.get_url(bookId)
        book["简介"] = book.get("intro")

        # 处理作者字段 - 可能为 None（本地书籍）
        author = book.get("author")
        if author:
            book["作者"] = [
                notion_helper.get_relation_id(
                    x, notion_helper.author_database_id, USER_ICON_URL
                )
                for x in author.split(" ")
            ]
        else:
            # 本地书籍可能没有作者信息，使用默认值
            book["作者"] = [
                notion_helper.get_relation_id(
                    "未知作者", notion_helper.author_database_id, USER_ICON_URL
                )
            ]
            if not bookId.startswith("CB_"):
                print(f"警告: 书籍 {bookId} 缺少作者信息，使用默认值")

        if book.get("categories"):
            book["分类"] = [
                notion_helper.get_relation_id(
                    x.get("title"), notion_helper.category_database_id, TAG_ICON_URL
                )
                for x in book.get("categories")
            ]
    properties = utils.get_properties(book, book_properties_type_dict)
    if book.get("时间"):
        notion_helper.get_date_relation(
            properties,
            pendulum.from_timestamp(book.get("时间"), tz="Asia/Shanghai"),
        )

    title = book.get('title') or f"未知书名-{bookId}"
    print(f"正在插入《{title}》,一共{len(books)}本，当前是第{index+1}本。")
    parent = {"database_id": notion_helper.book_database_id, "type": "database_id"}
    result = None
    if bookId in notion_books:
        result = notion_helper.update_page(
            page_id=notion_books.get(bookId).get("pageId"),
            properties=properties,
            cover=utils.get_icon(cover),
        )
    else:
        result = notion_helper.create_book_page(
            parent=parent,
            properties=properties,
            icon=utils.get_icon(cover),
        )
    page_id = result.get("id")
    if book.get("readDetail") and book.get("readDetail").get("data"):
        data = book.get("readDetail").get("data")
        data = {item.get("readDate"): item.get("readTime") for item in data}
        insert_read_data(page_id, data)


def insert_read_data(page_id, readTimes):
    readTimes = dict(sorted(readTimes.items()))
    filter = {"property": "书架", "relation": {"contains": page_id}}
    results = notion_helper.query_all_by_book(notion_helper.read_database_id, filter)
    for result in results:
        timestamp = result.get("properties").get("时间戳").get("number")
        duration = result.get("properties").get("时长").get("number")
        id = result.get("id")
        if timestamp in readTimes:
            value = readTimes.pop(timestamp)
            if value != duration:
                insert_to_notion(
                    page_id=id,
                    timestamp=timestamp,
                    duration=value,
                    book_database_id=page_id,
                )
    for key, value in readTimes.items():
        insert_to_notion(None, int(key), value, page_id)


def insert_to_notion(page_id, timestamp, duration, book_database_id):
    parent = {"database_id": notion_helper.read_database_id, "type": "database_id"}
    properties = {
        "标题": utils.get_title(
            pendulum.from_timestamp(timestamp, tz=tz).to_date_string()
        ),
        "日期": utils.get_date(
            start=pendulum.from_timestamp(timestamp, tz=tz).format(
                "YYYY-MM-DD HH:mm:ss"
            )
        ),
        "时长": utils.get_number(duration),
        "时间戳": utils.get_number(timestamp),
        "书架": utils.get_relation([book_database_id]),
    }
    if page_id != None:
        notion_helper.client.pages.update(page_id=page_id, properties=properties)
    else:
        notion_helper.client.pages.create(
            parent=parent,
            icon=utils.get_icon("https://www.notion.so/icons/target_red.svg"),
            properties=properties,
        )


weread_api = WeReadApi()
notion_helper = NotionHelper()
archive_dict = {}
notion_books = {}
books_metadata = {}  # 存储从 entire_shelf 获取的书籍元数据


def main():
    global notion_books
    global archive_dict
    global books_metadata

    # 原始方法：获取笔记本书架
    bookshelf_books = weread_api.get_bookshelf()

    # 获取完整书架（包含本地书籍）
    entire_shelf = None
    try:
        entire_shelf = weread_api.get_entire_shelf()
        # 提取书籍元数据（特别是本地书籍的基础信息）
        if entire_shelf and entire_shelf.get("books"):
            for book_data in entire_shelf["books"]:
                book_id = book_data.get("bookId")
                if book_id:
                    books_metadata[book_id] = book_data
    except Exception as e:
        print(f"获取完整书架失败，回退到笔记本书架: {e}")
        entire_shelf = None

    notion_books = notion_helper.get_all_book()

    # 处理bookProgress - 优先使用 entire_shelf，回退到 bookshelf_books
    bookProgress = None
    if entire_shelf and entire_shelf.get("bookProgress"):
        bookProgress = entire_shelf.get("bookProgress")
    else:
        bookProgress = bookshelf_books.get("bookProgress")

    if bookProgress is None:
        print("警告: 未找到bookProgress数据，使用空数据继续")
        bookProgress = {}
    else:
        bookProgress = {book.get("bookId"): book for book in bookProgress}

    # 处理archive - 优先使用 entire_shelf，回退到 bookshelf_books
    archives = None
    if entire_shelf and entire_shelf.get("archive"):
        archives = entire_shelf.get("archive")
    else:
        archives = bookshelf_books.get("archive")

    if archives is None:
        print("警告: 未找到archive数据，跳过书架分类")
    else:
        for archive in archives:
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
            and (value.get("cover") is not None)
            and (
                value.get("status") != "已读"
                or (value.get("status") == "已读" and value.get("myRating"))
            )
        ):
            not_need_sync.append(key)

    notebooks = weread_api.get_notebooklist()
    notebooks = [d["bookId"] for d in notebooks if "bookId" in d]

    # 合并书籍来源
    books_from_bookshelf = bookshelf_books.get("books", [])
    books_from_bookshelf = [d["bookId"] for d in books_from_bookshelf if "bookId" in d]

    # 如果成功获取 entire_shelf，合并其书籍
    if entire_shelf and entire_shelf.get("books"):
        books_from_entire = [d["bookId"] for d in entire_shelf.get("books") if "bookId" in d]
        # 合并所有书籍ID（去重）
        all_book_ids = set(notebooks) | set(books_from_bookshelf) | set(books_from_entire)
    else:
        # 回退到原有逻辑
        all_book_ids = set(notebooks) | set(books_from_bookshelf)

    books = list(all_book_ids - set(not_need_sync))

    for index, bookId in enumerate(books):
        insert_book_to_notion(books, index, bookId)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("微信读书书籍同步工具")
        print("用法: python -m weread2notionpro.book")
        print("功能: 同步微信读书的书籍信息到Notion")
        sys.exit(0)
    main()
