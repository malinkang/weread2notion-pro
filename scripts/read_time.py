import argparse
from datetime import datetime
from datetime import timedelta
import json
import os
import time

import pendulum

from notion_helper import NotionHelper
from weread_api import WeReadApi
from utils import format_date, get_date, get_icon, get_number, get_relation, get_title,upload_image

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


def get_file():
    # 设置文件夹路径
    folder_path = './OUT_FOLDER'

    # 检查文件夹是否存在
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        entries = os.listdir(folder_path)
        
        file_name = entries[0] if entries else None
        return file_name
    else:
        print("OUT_FOLDER does not exist.")
        return None

if __name__ == "__main__":
    weread_cookie = os.getenv("WEREAD_COOKIE")
    notion_helper = NotionHelper()
    weread_api = WeReadApi()
    image_file = get_file()
    if image_file:
        image_url = upload_image(f"heatmap/{os.getenv('REPOSITORY').split('/')[0]}",image_file,f"./OUT_FOLDER/{image_file}")
        block_id = os.getenv("HEATMAP_BLOCK_ID")
        if block_id == None or block_id.strip() == "":
            block_id = notion_helper.image_dict.get("id")
        if(image_url and block_id):
            notion_helper.update_image_block_link(block_id,image_url)
    api_data = weread_api.get_api_data()
    readTimes = {int(key):value for key,value in api_data.get("readTimes").items()}
    now = pendulum.now('Asia/Shanghai').start_of('day')
    today_timestamp = now.int_timestamp
    if(today_timestamp not in readTimes):
        readTimes[today_timestamp] = 0
    readTimes = dict(sorted(readTimes.items()))
    results =  notion_helper.query_all(database_id=notion_helper.day_database_id)
    for result in results:
        timestamp = result.get("properties").get("时间戳").get("number")
        duration = result.get("properties").get("时长").get("number")
        id = result.get("id")
        if(timestamp in readTimes):
            value = readTimes.pop(timestamp)
            if(value !=duration):
                insert_to_notion(page_id=id,timestamp=timestamp,duration=value)
    for key,value in readTimes.items():
        insert_to_notion(None,int(key),value)
