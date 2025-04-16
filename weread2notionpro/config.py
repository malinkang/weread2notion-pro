
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
    "书名":TITLE,
    "BookId":RICH_TEXT,
    "ISBN":RICH_TEXT,
    "链接":URL,
    "作者":RELATION,
    "Sort":NUMBER,
    "评分":NUMBER,
    "封面":FILES,
    "分类":RELATION,
    "阅读状态":STATUS,
    "阅读时长":NUMBER,
    "阅读进度":NUMBER,
    "阅读天数":NUMBER,
    "时间":DATE,
    "开始阅读时间":DATE,
    "最后阅读时间":DATE,
    "简介":RICH_TEXT,
    "书架分类":SELECT,
    "我的评分":SELECT,
    "豆瓣链接":URL,
}
tz='Asia/Shanghai' 