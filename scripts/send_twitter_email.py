#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送 Twitter Home Timeline 邮件
"""

import smtplib
import subprocess
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# 配置
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "370583129@qq.com"
ATTACHMENT_PATH = "/Users/wcb/.openclaw/workspace/x.md"

def get_password():
    """从钥匙串获取密码"""
    result = subprocess.run(
        ["security", "find-generic-password", "-a", SMTP_USER, "-s", "himalaya-imap-qq", "-w"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def send_email_with_attachment():
    """发送带附件的邮件"""
    password = get_password()
    
    msg = MIMEMultipart()
    msg['From'] = f"OpenClaw <{SMTP_USER}>"
    msg['To'] = SMTP_USER
    msg['Subject'] = f"Twitter Home Timeline - {sys.argv[1] if len(sys.argv) > 1 else '2026-02-26'}"
    
    # 添加邮件正文
    body = """Twitter Home Timeline 已获取成功！

共 100 条动态，详见附件 x.md 文件。

以下是前 5 条动态预览：
"""
    
    # 读取 x.md 前 500 行作为预览
    try:
        with open(ATTACHMENT_PATH, 'r', encoding='utf-8') as f:
            preview = ''.join(f.readlines()[:50])
            body += "\n" + preview[:2000] + "\n\n...（更多内容请查看附件）"
    except Exception as e:
        body += f"\n预览失败：{e}"
    
    body += "\n\n--\n卡卡 👾"
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 添加附件
    try:
        with open(ATTACHMENT_PATH, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="x.md"')
        msg.attach(part)
        print(f"📎 附件已添加：x.md")
    except Exception as e:
        print(f"❌ 附件添加失败：{e}")
        return False
    
    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ 邮件发送成功！")
        print(f"   收件人：{SMTP_USER}")
        print(f"   主题：{msg['Subject']}")
        return True
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        return False

if __name__ == "__main__":
    success = send_email_with_attachment()
    sys.exit(0 if success else 1)
