import pymysql
from config import DB_CONFIG
from fetch_mail import fetch_latest_email
from summarize_ai import process_email
from imapclient import IMAPClient

def get_all_mailboxes():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id, provided_address, provided_password FROM mailbox")
    mailboxes = cursor.fetchall()
    conn.close()
    return mailboxes

def get_processed_mail_ids(mailbox_id):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT mail_id FROM todo WHERE mailbox_id=%s", (mailbox_id,))
    processed = {row[0] for row in cursor.fetchall()}
    conn.close()
    return processed

def fetch_and_summarize_all_mailboxes():
    mailboxes = get_all_mailboxes()
    for mailbox_id, email, password in mailboxes:
        print(f"处理邮箱: {email}")
        try:
            with IMAPClient('mail.34555.net') as client:
                client.login(email, password)
                client.select_folder('INBOX')
                uids = client.search(['NOT', 'DELETED'])
                processed_uids = get_processed_mail_ids(mailbox_id)
                new_uids = [uid for uid in uids if str(uid) not in processed_uids]
                print(f"新邮件UID: {new_uids}")
                for uid in new_uids:
                    raw_msg = client.fetch([uid], ['RFC822'])[uid][b'RFC822']
                    import mailparser
                    parsed = mailparser.parse_from_bytes(raw_msg)
                    subject = parsed.subject or ""
                    body = parsed.body or ""
                    content = f"{subject}\n\n{body}"
                    # 用UID作为mail_id
                    process_email(mail_id=str(uid), mailbox_id=mailbox_id, content=content)
                    print(f"已处理邮件UID: {uid}")
        except Exception as e:
            print(f"处理 {email} 时出错: {e}")

if __name__ == "__main__":
    fetch_and_summarize_all_mailboxes()
