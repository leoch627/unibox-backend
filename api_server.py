from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fetch_mail import fetch_latest_email
from create_user import create_mail_user_if_not_exists, create_user
import pymysql
from config import DB_CONFIG
from summarize_ai import get_important_details_by_mailbox, get_todos_by_mailbox
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定你的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class UpdateIsCheckedRequest(BaseModel):
    todo_id: int
    ischecked: bool

class MailRequest(BaseModel):
    email: str
    password: str

class RegisterUserRequest(BaseModel):
    email: str
    password: str

class CreateUserRequest(BaseModel):
    name: str
    student_id: str

class RegisterMailboxRequest(BaseModel):
    user_id: str
    prefix: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/fetch-latest-email/")
def fetch_mail_endpoint(req: MailRequest):
    """
    获取指定邮箱的最新邮件内容。
    参数: email, password
    返回: 邮件内容字符串
    """
    try:
        result = fetch_latest_email(req.email, req.password)
        if result is None:
            raise HTTPException(status_code=404, detail="No email found")
        return {"content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/todo/update-ischecked/")
def update_ischecked(req: UpdateIsCheckedRequest):
    """
    更改todo的ischecked状态。
    参数: todo_id, ischecked
    返回: 操作结果
    """
    try:
        update_todo(req.todo_id, ischecked=req.ischecked)
        return {"msg": "ischecked状态已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register-mailbox/")
def register_mailbox(req: RegisterMailboxRequest):
    """
    注册新邮箱账号并与用户关联。
    参数: user_id, prefix, password
    返回: 创建结果信息和mailbox_id
    """
    try:
        mailbox_id = create_mail_user_if_not_exists(req.user_id, req.prefix, req.password)
        if not mailbox_id:
            raise HTTPException(status_code=400, detail="邮箱已被占用或用户不存在")
        return {"msg": "邮箱创建成功", "mailbox_id": mailbox_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register-user/")
def register_user(req: RegisterUserRequest):
    """
    注册新用户。
    参数: email, password
    返回: 创建结果信息和用户ID
    """
    try:
        user_id = create_user(req.email, req.password)
        return {"msg": "用户创建成功", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mailbox/{mailbox_id}/summaries/")
def get_summaries(mailbox_id: str):
    """
    查询某邮箱下所有邮件的摘要和处理状态（todo表）。
    参数: mailbox_id
    返回: 每封邮件的 mail_id、summary_text、ischecked
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        todos = get_todos_by_mailbox(conn, mailbox_id)
        result = []
        for mail_id, summary_text, ischecked in todos:
            result.append({
                "mail_id": mail_id,
                "summary_text": summary_text,
                "ischecked": bool(ischecked)
            })
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mailbox/{mailbox_id}/important-details/")
def get_important_details(mailbox_id: str):
    """
    查询某邮箱下所有关键信息（key-value）。
    参数: mailbox_id
    返回: key-value 数组
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        details = get_important_details_by_mailbox(conn, mailbox_id)
        result = []
        for key, value in details:
            result.append({"key": key, "value": value})
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/list/")
def user_list():
    """
    查询所有用户信息。
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM users")
        users = [{"id": row[0], "email": row[1]} for row in cursor.fetchall()]
        conn.close()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login/")
def login(req: LoginRequest):
    """
    用户登录接口。
    参数: email, password
    返回: 登录结果（用户ID）
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email=%s", (req.email,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            raise HTTPException(status_code=401, detail="用户不存在或密码错误")
        user_id, db_password = row
        if req.password != db_password:
            raise HTTPException(status_code=401, detail="用户不存在或密码错误")
        return {"msg": "登录成功", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
