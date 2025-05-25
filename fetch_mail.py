from imapclient import IMAPClient
import mailparser
from bs4 import BeautifulSoup
import html2text
import pymysql

def fetch_latest_email(email, password):
    with IMAPClient('mail.34555.net') as client:
        client.login(email, password)
        client.select_folder('INBOX')
        messages = client.search(['NOT', 'DELETED'])
        if not messages:
            return None
        
        msg_id = messages[-1]
        raw_msg = client.fetch([msg_id], ['RFC822'])[msg_id][b'RFC822']
        parsed = mailparser.parse_from_bytes(raw_msg)
        
        # Extract subject
        subject = parsed.subject
        
        # Handle HTML content with BeautifulSoup
        html_content = parsed.body
        if html_content:
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Convert any remaining HTML entities
            h = html2text.HTML2Text()
            h.ignore_links = False
            clean_text = h.handle(text)
            
            # Return as a simple string format
            return f"{subject}\n\n{clean_text}"
        
        # If no HTML content, return simple text format
        return f"{subject}\n\n{parsed.body}"

# Example usage:
# email_body = fetch_latest_email("student001@example.com", "Password123")

def add_todo(mail_id, summary_text, mailbox_id, ischecked=False):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todo (mail_id, summary_text, ischecked, mailbox_id) VALUES (%s, %s, %s, %s)",
        (mail_id, summary_text, ischecked, mailbox_id)
    )
    conn.commit()
    conn.close()
