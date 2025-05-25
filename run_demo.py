from fetch_mail import fetch_latest_email
from summarize_ai import extract_summary_and_keys, process_email

email = "admin@34555.net"
password = "2773zrS8M}"
mailbox_id = 1  # 这里需要你实际传入对应的mailbox_id

content = fetch_latest_email(email, password)
if content:
    # 提取摘要和关键信息
    result = extract_summary_and_keys(content)
    print("📌 AI摘要:", result.get('summary', ''))
    print("📌 关键信息:")
    for item in result.get('keys', []):
        print(f"- {item.get('key')}: {item.get('value')}")
    
    # 写入数据库
    process_email(mailbox_id, subject="(自动获取或填写邮件主题)", body=content)
else:
    print("📭 无新邮件")
