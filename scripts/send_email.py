#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 SMTP 直接发送邮件（不依赖 himalaya）
支持从 stdin 读取邮件内容（用于 himalaya 集成）
支持附件发送
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
SMTP_PORT = 587
SMTP_USER = "370583129@qq.com"

def get_password():
    """从钥匙串获取密码"""
    result = subprocess.run(
        ["security", "find-generic-password", "-a", SMTP_USER, "-s", "himalaya-smtp-qq", "-w"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def send_email_raw(raw_email):
    """发送原始邮件（RFC 822 格式）"""
    password = get_password()
    
    try:
        # 连接 SMTP 服务器
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()  # 启用 TLS
        server.login(SMTP_USER, password)
        server.sendmail(SMTP_USER, [SMTP_USER], raw_email)
        server.quit()
        print("✅ 邮件发送成功！", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ 发送失败：{e}", file=sys.stderr)
        return False

def send_email_simple(to, subject, body, from_name="OpenClaw"):
    """发送简单邮件"""
    password = get_password()
    
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{SMTP_USER}>"
    msg['To'] = to
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ 邮件发送成功！")
        print(f"   收件人：{to}")
        print(f"   主题：{subject}")
        return True
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        return False

def send_email_with_attachment(to, subject, body, attachment_path, from_name="OpenClaw"):
    """发送带附件的邮件"""
    password = get_password()
    
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{SMTP_USER}>"
    msg['To'] = to
    msg['Subject'] = subject
    
    # 添加邮件正文
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 添加附件
    try:
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        filename = os.path.basename(attachment_path)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)
        
        print(f"📎 附件已添加：{filename}")
    except Exception as e:
        print(f"❌ 附件添加失败：{e}")
        return False
    
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ 邮件发送成功！")
        print(f"   收件人：{to}")
        print(f"   主题：{subject}")
        print(f"   附件：{os.path.basename(attachment_path)}")
        return True
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        return False

if __name__ == "__main__":
    # 如果有命令行参数，使用简单模式
    if len(sys.argv) >= 4:
        to = sys.argv[1]
        subject = sys.argv[2]
        body = sys.argv[3]
        send_email_simple(to, subject, body)
    # 如果从 stdin 读取（himalaya 模式）
    elif not sys.stdin.isatty():
        raw_email = sys.stdin.read()
        send_email_raw(raw_email)
    else:
        # 默认测试
        send_email_simple(SMTP_USER, "OpenClaw 测试邮件", "这是一封测试邮件！")
