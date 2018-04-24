# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

from celery import Celery
from django.core.mail import send_mail
from dailyfresh import settings
# 创建celery客户段
app = Celery('dailyfresh', broker='redis://127.0.0.1:6379/1')


@app.task
def send_active_mail(username, email, token):
    """发送激活邮件"""
    subject = "天天生鲜用户激活"  # 标题
    message = ""  # 邮件正文(纯文本)
    from_email = settings.EMAIL_FROM  # 发件人
    recipient_list = [email]  # 接收人, 需要是列表
    # 邮件正文(带html样式)
    html_message = ('<h2>尊敬的 %s, 感谢注册天天生鲜</h2>' 
                    '请点击此链接激活您的帐号: <br/>' 
                    '<a href="http://127.0.0.1:8000/users/active/%s">' 
                    'http://127.0.0.1:8000/users/active/%s</a>'
                    ) % (username, token, token)
    send_mail(subject, message, from_email, recipient_list, html_message=html_message)