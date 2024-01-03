import argparse
from datetime import datetime
from datetime import timedelta
import os

from notion_helper import NotionHelper
from weread_api import WeReadApi
from utils import format_date, get_date, get_icon, get_number, get_relation, get_title

def insert_to_notion(page_id,timestamp,duration):
    parent = {"database_id": notion_helper.day_database_id, "type": "database_id"}
    properties = {
        "标题": get_title(format_date(datetime.utcfromtimestamp(timestamp)+timedelta(hours=8),"%Y年%m月%d日")),
        "日期": get_date(start = format_date(datetime.utcfromtimestamp(timestamp)+timedelta(hours=8))),
        "时长": get_number(duration),
        "时间戳": get_number(timestamp),
        "年":get_relation(
            [
                notion_helper.get_year_relation_id(datetime.utcfromtimestamp(timestamp)+timedelta(hours=8)),
            ]
        ),
        "月":get_relation(
            [
                notion_helper.get_month_relation_id(datetime.utcfromtimestamp(timestamp)+timedelta(hours=8)),
            ]
        ),
        "周":get_relation(
            [
                notion_helper.get_week_relation_id(datetime.utcfromtimestamp(timestamp)+timedelta(hours=8)),
            ]
        )
        
    }
    if page_id!=None:
        notion_helper.client.pages.update(page_id=page_id, properties=properties)
    else:
        notion_helper.client.pages.create(parent=parent,icon = get_icon("https://www.notion.so/icons/target_red.svg"),properties=properties)


if __name__ == "__main__":
    weread_cookie = os.getenv("WEREAD_COOKIE")
    notion_helper = NotionHelper()
    weread_api = WeReadApi()
    api_data = weread_api.get_api_data()
    readTimes = dict(sorted(api_data["readTimes"].items()))
    print(f"readTimes {len(readTimes)}")
    results =  notion_helper.query_all(database_id=notion_helper.day_database_id)
    for result in results:
        timestamp = result.get("properties").get("时间戳").get("number")
        duration = result.get("properties").get("时长").get("number")
        id = result.get("id")
        if(str(timestamp) in readTimes):
            value = readTimes.pop(str(timestamp))
            print(value)
            if(value !=duration):
                insert_to_notion(page_id=id,timestamp=timestamp,duration=value)
    for key,value in readTimes.items():
        insert_to_notion(None,int(key),value)
