import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def send_email_if_signal(message, image_path):
    sender = os.getenv("QQ_EMAIL")
    password = os.getenv("AUTH_CODE")
    receiver = os.getenv("RECEIVER")

    if not sender or not password or not receiver:
        print("❌ 缺少邮件环境变量（QQ_EMAIL / AUTH_CODE / RECEIVER）")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "【买入信号】长江电力站上60日线"

    msg.attach(MIMEText(message, "plain", "utf-8"))

    with open(image_path, "rb") as f:
        img = MIMEApplication(f.read())
        img.add_header("Content-Disposition", "attachment", filename="ma60_chart.png")
        msg.attach(img)

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("📩 邮件发送成功。")
    except Exception as e:
        print("❌ 邮件发送失败：", e)
