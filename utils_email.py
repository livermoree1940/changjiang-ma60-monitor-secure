import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import socket

def send_email_if_signal(message, image_path=None):
    sender = os.getenv("QQ_EMAIL")
    password = os.getenv("AUTH_CODE")
    receiver = os.getenv("RECEIVER")

    print(f"邮件配置检查 - 发件人: {sender}, 收件人: {receiver}")

    if not sender or not password or not receiver:
        print("❌ 缺少邮件环境变量（QQ_EMAIL / AUTH_CODE / RECEIVER）")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = "【股票买入信号提醒】"

        msg.attach(MIMEText(message, "plain", "utf-8"))

        # 如果有图片附件
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as f:
                    img = MIMEApplication(f.read())
                    img.add_header("Content-Disposition", "attachment", filename=os.path.basename(image_path))
                    msg.attach(img)
                print(f"✅ 成功添加图片附件: {image_path}")
            except Exception as e:
                print(f"❌ 添加图片附件失败: {e}")

        # 设置更长的超时时间
        socket.setdefaulttimeout(30)
        
        # 尝试多种连接方式
        try:
            # 方式1: 使用SMTP_SSL
            print("尝试使用 SMTP_SSL 连接...")
            with smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30) as server:
                server.login(sender, password)
                server.send_message(msg)
            print("📩 邮件发送成功！(SMTP_SSL)")
            return True
        except Exception as e1:
            print(f"SMTP_SSL 失败: {e1}")
            try:
                # 方式2: 使用STARTTLS
                print("尝试使用 STARTTLS 连接...")
                with smtplib.SMTP("smtp.qq.com", 587, timeout=30) as server:
                    server.starttls()
                    server.login(sender, password)
                    server.send_message(msg)
                print("📩 邮件发送成功！(STARTTLS)")
                return True
            except Exception as e2:
                print(f"STARTTLS 失败: {e2}")
                # 方式3: 使用25端口
                try:
                    print("尝试使用端口25连接...")
                    with smtplib.SMTP("smtp.qq.com", 25, timeout=30) as server:
                        server.login(sender, password)
                        server.send_message(msg)
                    print("📩 邮件发送成功！(Port 25)")
                    return True
                except Exception as e3:
                    print(f"端口25连接失败: {e3}")
                    print("❌ 所有邮件发送方式均失败")
                    return False
                    
    except Exception as e:
        print(f"❌ 邮件发送过程中发生异常: {e}")
        return False
