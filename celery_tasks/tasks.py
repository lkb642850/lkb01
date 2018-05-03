# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()
from time import sleep

from celery import Celery
from django.core.mail import send_mail
from django.shortcuts import render
from django.template import loader
from requests import request

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods
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


@app.task
def generate_static_index_page():
    """生成静态首页"""
    sleep(2)

    # 查询商品类别数据  代码和原来的首页代码一样，然后把代码渲染后执行到桌面路径
    categories = GoodsCategory.objects.all()

    # 查询商品轮播轮数据
    slide_skus = IndexSlideGoods.objects.all().order_by('index')

    # 查询商品促销活动数据
    promotions = IndexPromotion.objects.all().order_by('index')

    for c in categories:
        # 查询当前类型所以的文字类型和图片 0代表文字，1 代表图片
        text_skus = IndexCategoryGoods.objects.filter(
            display_type=0, category=c)
        image_skus = IndexCategoryGoods.objects.filter(
            display_type=1, category=c)[0:4]
        # 动态给对象新增实例属性
        c.text_skus = text_skus
        c.image_skus = image_skus
    cart_count = 0
    context = {
        'categories': categories,
        'slide_skus': slide_skus,
        'promotions': promotions,
        'cart_count': cart_count,
    }

    # 渲染生成静态的首页
    template = loader.get_template('index.html')
    html_str = template.render(context)
    # 生成首页
    path = '/home/python/Desktop/static/index.html'
    with open(path, 'w') as file:
        file.write(html_str)