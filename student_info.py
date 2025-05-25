import pymysql
from config import DB_CONFIG

def insert_user_info(name, student_id):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, student_id) VALUES (%s, %s)",
        (name, student_id)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def insert_mailbox_info(user_id, email, password):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mailbox (user_id, provided_email, provided_password) VALUES (%s, %s, %s)",
        (user_id, email, password)
    )
    conn.commit()
    mailbox_id = cursor.lastrowid
    conn.close()
    return mailbox_id