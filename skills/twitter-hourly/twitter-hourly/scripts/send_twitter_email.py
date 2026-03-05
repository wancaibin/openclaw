#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送 Twitter Home Timeline 邮件
"""

import smtplib
import subprocess
import sys
import os
import zipfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# 配置
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "370583129@qq.com"
ATTACHMENT_PATH = "/Users/wcb/.openclaw/workspace/x.md"
ZIP_PATH = "/Users/wcb/.openclaw/workspace/x.zip"

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
    
    # 邮件正文留空，只发附件
    body = ""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 压缩文件并添加为附件
    try:
        # 创建 zip 压缩包
        with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(ATTACHMENT_PATH, 'x.md')
        
        print(f"📦 已压缩：x.md → x.zip")
        
        # 添加 zip 附件
        with open(ZIP_PATH, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="x.zip"')
        msg.attach(part)
        print(f"📎 附件已添加：x.zip")
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
