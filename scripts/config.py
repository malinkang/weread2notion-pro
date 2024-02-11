
RICH_TEXT = "rich_text"
URL = "url"
RELATION = "relation"
NUMBER = "number"
DATE = "date"
FILES = "files"
STATUS = "status"
TITLE = "title"
SELECT = "select"

book_properties_type_dict = {
    "图书名称":TITLE,
    "图书 ID":RICH_TEXT,
    "ISBN":RICH_TEXT,
    "图书链接":URL,
    "作者":RELATION,
    "排序标记":NUMBER,
    "大众评分":NUMBER,
    "图书封面":FILES,
    "微读分类":RELATION,
    "阅读状态":STATUS,
    "微读时长":NUMBER,
    "阅读进度":NUMBER,
    "阅读天数":NUMBER,
    "阅读时间":DATE,
    "开始阅读时间":DATE,
    "最后阅读时间":DATE,
    "内容简介":RICH_TEXT,
    "书架分类":SELECT,
    "个人评级":SELECT,
    "豆瓣链接":URL,
}
