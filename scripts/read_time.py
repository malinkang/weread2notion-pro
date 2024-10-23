import argparse
from datetime import datetime
from datetime import timedelta
import json
import os
import time

import pendulum

from notion_helper import NotionHelper
from weread_api import WeReadApi
from utils import (
    format_date,
    get_date,
    get_icon,
    get_number,
    get_relation,
    get_title,
    get_embed,
)


def insert_to_notion(page_id, timestamp, duration):
    parent = {"database_id": notion_helper.day_database_id, "type": "database_id"}
    properties = {
        "标题": get_title(
            format_date(
                datetime.utcfromtimestamp(timestamp) + timedelta(hours=8),
                "%Y年%m月%d日",
            )
        ),
        "日期": get_date(
            start=format_date(datetime.utcfromtimestamp(timestamp) + timedelta(hours=8))
        ),
        "时长": get_number(duration),
        "时间戳": get_number(timestamp),
        "年": get_relation(
            [
                notion_helper.get_year_relation_id(
                    datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)
                ),
            ]
        ),
        "月": get_relation(
            [
                notion_helper.get_month_relation_id(
                    datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)
                ),
            ]
        ),
        "周": get_relation(
            [
                notion_helper.get_week_relation_id(
                    datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)
                ),
            ]
        ),
    }
    if page_id != None:
        notion_helper.client.pages.update(page_id=page_id, properties=properties)
    else:
        notion_helper.client.pages.create(
            parent=parent,
            icon=get_icon("https://www.notion.so/icons/target_red.svg"),
            properties=properties,
        )


def get_file():
    # 设置文件夹路径
    folder_path = "./OUT_FOLDER"

    # 检查文件夹是否存在
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        entries = os.listdir(folder_path)

        file_name = entries[0] if entries else None
        return file_name
    else:
        print("OUT_FOLDER does not exist.")
        return None

HEATMAP_GUIDE = "https://mp.weixin.qq.com/s?__biz=MzI1OTcxOTI4NA==&mid=2247484145&idx=1&sn=81752852420b9153fc292b7873217651&chksm=ea75ebeadd0262fc65df100370d3f983ba2e52e2fcde2deb1ed49343fbb10645a77570656728&token=157143379&lang=zh_CN#rd"
if __name__ == "__main__":
    os.environ['NOTION_PAGE'] = 'Life-OS-System-81b25bbd21684a3c943eb03a44b2f900'
    os.environ['NOTION_TOKEN'] = 'secret_LAVFOz2S74ztgXTaDPuYKEjGEKPtflnk5IV0DbzW4vd'
    os.environ['WEREAD_COOKIE'] = 'ptcz=754d621bb3cc45abb68f07d842270b8db5224d5c18bc38c78d239f19edb36567; pgv_pvid=6811236617; _qimei_uuid42=17c02151133100c79dcf768330e7e363052c0fa717; _qimei_q36=; wr_gid=273651192; wr_theme=white; RK=QHthLXYzU2; pac_uid=0_3fbe47a232d9f; iip=0; suid=ek171315182328217824; wr_vid=68910221; wr_pf=0; wr_rt=web%40xEmeptoh5f57cXUSQSQ_AL; wr_localvid=be8325e0741b7c8dbe86f3b; wr_name=Easonlee; wr_gender=1; wr_avatar=https%3A%2F%2Fwx.qlogo.cn%2Fmmhead%2FcyiaTKm65RvUN6Mnm27TwKefnx3fCSsEClhwOuysFbHw%2F0; qq_domain_video_guid_verify=aef172aa1a598b90; _ga=GA1.2.1031625882.1723940499; _ga_8YVFNWD1KC=GS1.2.1723940499.1.1.1723940531.0.0.0; _clck=3911196076|1|fon|0; _qimei_fingerprint=88a18db09377adee6270beae94358cff; _qimei_h38=b115791b9dcf768330e7e36303000006617c02; wr_fp=25923672; wr_skey=7SD1H2_a'
    notion_helper = NotionHelper()
    weread_api = WeReadApi()
    #image_file = get_file()
    #if image_file:
    #    image_url = f"https://raw.githubusercontent.com/{os.getenv('REPOSITORY')}/{os.getenv('REF').split('/')[-1]}/OUT_FOLDER/{image_file}"
    #    heatmap_url = f"https://heatmap.malinkang.com/?image={image_url}"
    #    if notion_helper.heatmap_block_id:
    #        response = notion_helper.update_heatmap(
    #            block_id=notion_helper.heatmap_block_id, url=heatmap_url
    #        )
    #    else:
    #        print(f"更新热力图失败，没有添加热力图占位。具体参考：{HEATMAP_GUIDE}")
    #else:
    #    print(f"更新热力图失败，没有生成热力图。具体参考：{HEATMAP_GUIDE}")
    api_data = weread_api.get_api_data()
    readTimes = {int(key): value for key, value in api_data.get("readTimes").items()}
    now = pendulum.now("Asia/Shanghai").start_of("day")
    today_timestamp = now.int_timestamp
    if today_timestamp not in readTimes:
        readTimes[today_timestamp] = 0
    readTimes = dict(sorted(readTimes.items()))
    results = notion_helper.query_all(database_id=notion_helper.day_database_id)
    for result in results:
        timestamp = result.get("properties").get("时间戳").get("number")
        duration = result.get("properties").get("时长").get("number")
        id = result.get("id")
        if timestamp in readTimes:
            value = readTimes.pop(timestamp)
            if value != duration:
                insert_to_notion(page_id=id, timestamp=timestamp, duration=value)
    for key, value in readTimes.items():
        insert_to_notion(None, int(key), value)
