import openai
import pymysql
from config import DB_CONFIG, DB_CONFIG
import requests
import uuid


ALIYUN_API_KEY = "sk-a9753906bf304aed9aaa799cce312f5d"

def ali_qwen_chat(prompt, api_key, model="qwen-turbo"):
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "input": {
            "prompt": prompt
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    # 解析返回内容
    return result["output"]["text"]

def extract_summary_and_keys(content):
    prompt = f"""请从以下邮件内容中完成以下两项任务：1.总结一段简明摘要；2.提取所有与学生有关的关键信息（如government ID、学校后台密码、学号、姓名等），以key-value形式输出；如未找到相关信息，可省略该字段。\n\n邮件内容如下：\n{content}\n\n请用如下JSON格式返回：\n{{"summary":"...","keys":[{{"key":"...","value":"..."}}]}}  //若无关键信息则可省略此数组或返回空数组"""

    result_text = ali_qwen_chat(prompt, ALIYUN_API_KEY)
    print("阿里云原始返回：", repr(result_text))  # 打印原始返回内容
    # 去除 markdown 代码块包裹
    result_text = result_text.strip()
    if result_text.startswith("```json"):
        result_text = result_text[len("```json"):].strip()
    if result_text.startswith("```"):
        result_text = result_text[len("```"):].strip()
    if result_text.endswith("```"):
        result_text = result_text[:-3].strip()
    import json
    # 兼容单引号JSON
    result = result_text.replace("'", '"')
    return json.loads(result)

def insert_important_detail(conn, mailbox_id, info_key, info_value):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO important_details (mailbox_id, info_key, info_value) VALUES (%s, %s, %s)",
        (mailbox_id, info_key, info_value)
    )
    conn.commit()
    return cursor.lastrowid

def insert_todo(conn, mail_id, summary_text, mailbox_id, ischecked=False):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todo (mail_id, summary_text, ischecked, mailbox_id) VALUES (%s, %s, %s, %s)",
        (mail_id, summary_text, ischecked, mailbox_id)
    )
    conn.commit()
    return cursor.lastrowid

def process_email(mail_id, mailbox_id, content):
    conn = pymysql.connect(**DB_CONFIG)
    ai_result = extract_summary_and_keys(content)
    summary = ai_result.get('summary', '')
    keys = ai_result.get('keys', [])
    # 插入todo表
    insert_todo(conn, mail_id, summary, mailbox_id, ischecked=False)
    # 插入所有关键信息到important_details
    for item in keys:
        insert_important_detail(conn, mailbox_id, item.get('key'), item.get('value'))
    conn.close()
    print(f"AI摘要和关键信息已写入数据库，mail_id={mail_id}")

def get_important_details_by_mailbox(conn, mailbox_id):
    """
    根据 mailbox_id 查询 important_details 表，返回 (info_key, info_value) 元组列表。
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT info_key, info_value FROM important_details WHERE mailbox_id=%s",
        (mailbox_id,)
    )
    return cursor.fetchall()

def get_todos_by_mailbox(conn, mailbox_id):
    """
    根据 mailbox_id 查询 todo 表，返回 (mail_id, summary_text, ischecked) 元组列表。
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mail_id, summary_text, ischecked FROM todo WHERE mailbox_id=%s",
        (mailbox_id,)
    )
    return cursor.fetchall()

# 示例用法：
# process_email(mail_id="<Message-ID>", mailbox_id="mailbox-uuid", content="邮件正文内容")
