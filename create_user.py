import pymysql
from config import DB_CONFIG, DB_CONFIG_VMAIL
import uuid
from datetime import datetime
import hashlib
import base64
import os

def dovecot_ssha512(password):
    salt = os.urandom(16)
    hash = hashlib.sha512(password.encode('utf-8') + salt).digest()
    return '{SSHA512}' + base64.b64encode(hash + salt).decode('utf-8')

def make_maildir(prefix):
    now = datetime.now().strftime('%Y.%m.%d.%H.%M.%S')
    segs = [(prefix[i] if i < len(prefix) else '_') for i in range(3)]
    return f"34555.net/{segs[0]}/{segs[1]}/{segs[2]}/{prefix}-{now}/"

def create_mail_user_if_not_exists(user_id, prefix, password):
    email = f"{prefix}@34555.net"
    # 检查邮箱是否已存在
    conn_vmail = pymysql.connect(**DB_CONFIG_VMAIL)
    cursor_vmail = conn_vmail.cursor()
    cursor_vmail.execute("SELECT username FROM mailbox WHERE username=%s", (email,))
    if cursor_vmail.fetchone():
        print(f"邮箱 {email} 已被占用")
        conn_vmail.close()
        return False
    # 插入新邮箱账户，密码加密，maildir规范
    from uuid import uuid4
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    maildir = make_maildir(prefix)
    enc_password = dovecot_ssha512(password)
    sql = """
    INSERT INTO mailbox (
        username, password, name, language, mailboxformat, mailboxfolder,
        storagebasedirectory, storagenode, maildir, quota, domain, transport,
        department, rank, employeeid, isadmin, isglobaladmin, enablesmtp, enablesmtpsecured,
        enablepop3, enablepop3secured, enablepop3tls, enableimap, enableimapsecured, enableimaptls,
        enabledeliver, enablelda, enablemanagesieve, enablemanagesievesecured, enablesieve, enablesievesecured,
        enablesievetls, enableinternal, enabledoveadm, `enablelib-storage`, `enablequota-status`, `enableindexer-worker`,
        enablelmtp, enabledsync, enablesogo, enablesogowebmail, enablesogocalendar, enablesogoactivesync,
        passwordlastchange, created, modified, expired, active
    ) VALUES (
        %s, %s, %s, 'en_US', 'maildir', 'Maildir',
        '/var/vmail', 'vmail1', %s, 1024, '34555.net', '', '', 'normal', '', 0, 0, 1, 1,
        1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1,
        1, 1, 1, 'y', 'y', 'y',
        %s, %s, %s, '9999-12-31 00:00:00', 1
    )
    """
    cursor_vmail.execute(sql, (
        email, enc_password, prefix, maildir,
        now, now, now
    ))
    conn_vmail.commit()
    conn_vmail.close()
    print(f"邮箱账户 {email} 创建成功")
    # 生成mailbox_id，写入ai_data数据库mailbox表
    mailbox_id = str(uuid4())
    conn_ai = pymysql.connect(**DB_CONFIG)
    cursor_ai = conn_ai.cursor()
    cursor_ai.execute(
        "INSERT INTO mailbox (id, user_id, provided_address, provided_password) VALUES (%s, %s, %s, %s)",
        (mailbox_id, user_id, email, password)
    )
    conn_ai.commit()
    conn_ai.close()
    print(f"ai_data.mailbox写入成功: user_id={user_id}, mailbox_id={mailbox_id}, address={email}")
    return mailbox_id

def create_user(email, password):
    id = str(uuid.uuid4())
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (id, email, password) VALUES (%s, %s, %s)", (id, email, password))
    conn.commit()
    conn.close()
    print(f"用户 {email} 创建成功，user_id={id}")
    return user_id

# 示例用法
# create_mail_user_if_not_exists("student001", "Password123")
