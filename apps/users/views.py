import re

from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired

from apps.users.models import User
from celery_tasks.tasks import send_active_mail
from dailyfresh import settings


def index(request):
    return HttpResponse("首页")


def register(request):
    return render(request, 'register.html')


def do_register(request):
    return HttpResponse("进入登录界面")


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """实现注册功能"""
        # 获取post请求参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get("allow")  # 用户勾选协议

        # todo: 检验参数合法性
        # 判断参数不能为空
        if not all([username, password, password2, email]):
            return render(request, 'register.html', {'errmsg': '参数不能为空'})
        # 2次密码一致
        if password != password2:
            return render(request, 'register.html', {'errmsg': '密码不一致'})

        # 邮箱合法
        if not re.match('^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱错误'})

        # 勾选
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请勾选用户协议'})

        # 处理业务：保存到数据库
        user = None
        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:  # 数据完整性错误
            # 判断注册用户是否已经存在
            return render(request, 'register.html', {'errmsg': '用户已存在'})
        # 修改用户的激活状态为未激活
        user.is_active = False
        user.save()

        # todo: 发送激活邮件
        token = user.generate_active_token()
        # RegisterView.send_active_mail(username,email,token)
        # 异步操作 celery 不会阻塞
        send_active_mail.delay(username,email,token)
        # 响应请求,返回html页面

        # 判断用户存在
        # 修改用户为未激活
        #
        # todo:发送激活邮箱
        return redirect(reverse("users:login"))
    # 静态方法
    @staticmethod
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


class ActiveView(View):
    """用户激活"""

    def get(self,request,token):
        try:
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600*24)
            dict_data=s.loads(token.encode())
        except SignatureExpired:
            return HttpResponse("激活链接已经失效")

        user_id = dict_data.get('confirm')

        User.objects.filter(id=user_id.update(is_active=True))
        return redirect(reverse("users:login"))



class LoginView(View):
    def get(self, request):
        """进入登录界面"""
        return render(request, 'login.html')

    def post(self, request):
        """处理登录操作"""

        # 获取登录参数
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 校验参数合法性
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '请求参数不完整'})

        # 通过 django 提供的authenticate方法，
        # 验证用户名和密码是否正确
        user = authenticate(username=username, password=password)

        # 用户名或密码不正确
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码不正确'})

        if not user.is_active:  # 注册账号未激活
            # 用户未激活
            return render(request, 'login.html', {'errmsg': '请先激活账号'})

        # 通过django的login方法，保存登录用户状态（使用session）
        login(request, user)

        # 响应请求，返回html界面 (进入首页)
        return redirect(reverse('goods:index'))