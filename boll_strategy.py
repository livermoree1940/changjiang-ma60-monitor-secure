import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def send_email_if_signal(message, image_path=None):
    sender = os.getenv("QQ_EMAIL")
    password = os.getenv("AUTH_CODE")
    receiver = os.getenv("RECEIVER")

    print(f"邮件配置检查 - 发件人: {sender}, 收件人: {receiver}")

    if not sender or not password or not receiver:
        print("❌ 缺少邮件环境变量（QQ_EMAIL / AUTH_CODE / RECEIVER）")
        print(f"当前环境变量 - QQ_EMAIL: {'已设置' if sender else '未设置'}, AUTH_CODE: {'已设置' if password else '未设置'}, RECEIVER: {'已设置' if receiver else '未设置'}")
        return False

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

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("📩 邮件发送成功！")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败：{e}")
        return False
