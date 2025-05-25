import pymysql
from config import DB_CONFIG
from fastapi import HTTPException

# 新增一条todo（邮件摘要）
def add_todo(mail_id, summary_text, mailbox_id, ischecked=False):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todo (mail_id, summary_text, ischecked, mailbox_id) VALUES (%s, %s, %s, %s)",
        (mail_id, summary_text, ischecked, mailbox_id)
    )
    conn.commit()
    conn.close()

# 更新todo摘要或处理状态
def update_todo(todo_id, summary_text=None, ischecked=None):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    if summary_text is not None:
        cursor.execute("UPDATE todo SET summary_text=%s WHERE id=%s", (summary_text, todo_id))
    if ischecked is not None:
        cursor.execute("UPDATE todo SET ischecked=%s WHERE id=%s", (ischecked, todo_id))
    conn.commit()
    conn.close()

# 删除todo
def delete_todo(todo_id):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todo WHERE id=%s", (todo_id,))
    conn.commit()
    conn.close()

# 查询某邮箱下所有todo（邮件摘要）
def get_todos_by_mailbox(mailbox_id):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT mail_id, summary_text, ischecked FROM todo WHERE mailbox_id=%s", (mailbox_id,))
    todos = cursor.fetchall()
    conn.close()
    return todos

# 标记某邮件为已处理
def check_todo(mail_id, mailbox_id):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todo SET ischecked=1 WHERE mail_id=%s AND mailbox_id=%s",
            (mail_id, mailbox_id)
        )
        conn.commit()
        conn.close()
        return {"msg": "已标记为已处理"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
