# 长江电力60日线买入（changjiang-ma60-monitor-secure）

自动检测长江电力（600900.SH）是否首次站上60日均线，并通过 QQ 邮箱发送图表通知。

---

## 🧩 功能
- 自动获取A股数据（Ashare）
- 计算60日均线
- 判断是否“今日新站上60日线”
- 生成图表 + 邮件发送提醒
- 支持 GitHub Actions 定时运行（每日 4 次）

---

## ⚙️ 本地测试
```bash
pip install -r requirements.txt

# 在终端中临时设置环境变量
set QQ_EMAIL=你的邮箱@qq.com
set AUTH_CODE=你的授权码
set RECEIVER=接收邮箱

python main.py
```

---

## ☁️ GitHub Actions 自动化
1. 上传到 GitHub 仓库
2. 在仓库 Settings → Secrets → Actions 中添加：
   - QQ_EMAIL
   - AUTH_CODE
   - RECEIVER
3. 自动运行时将从 Secrets 中读取。

---

## ⏰ 运行时间（工作日）
- 09:40
- 10:30
- 13:30
- 14:50

仅在“首次站上60日线”时发送提醒。
