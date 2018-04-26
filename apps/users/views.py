import re

from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired

from apps.goods.models import GoodsSKU
from apps.users.models import User, Address
from celery_tasks.tasks import send_active_mail
from dailyfresh import settings
from utils.common import LoginRequiredMixin


# def index(request):
#     return HttpResponse("首页")
#
#
# def register(request):
#     return render(request, 'register.html')
#
#
# def do_register(request):
#     return HttpResponse("进入登录界面")


class RegisterView(View):
    """注册页面"""

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
        send_active_mail.delay(username, email, token)
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

    def get(self, request, token):
        try:
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600 * 24)
            dict_data = s.loads(token.encode())
        except SignatureExpired:
            return HttpResponse("激活链接已经失效")

        user_id = dict_data.get('confirm')

        User.objects.filter(id=user_id.update(is_active=True))
        return redirect(reverse("users:login"))


class LoginView(View):
    """登陆视图"""
    def get(self, request):
        """进入登录界面"""
        return render(request, 'login.html')

    def post(self, request):
        """处理登录操作"""

        # 获取登录参数
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 校验参数合法性 ，如果参数不存在 返回登陆页面
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '请求参数不完整'})

        # 通过 django 提供的authenticate方法，
        # 验证用户名和密码是否正确
        user = authenticate(username=username, password=password)

        # 用户名或密码不正确，回到登陆页面 不用重定向是因为需要给提示信息
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码不正确'})

        if not user.is_active:  # 注册账号未激活
            # 用户未激活
            return render(request, 'login.html', {'errmsg': '请先激活账号'})

        # 通过django的login方法，保存登录用户状态（使用session）
        login(request, user)
        # 记住用户功能就是设置session有效期 # request.session.set_expiry(value) # 如果value是一个整数，那么会话将在value秒没有活动后过期
        # 如果value为0，那么会话的Cookie将在用户的浏览会话结束时过期 # 如果value为None，那么会话则两个星期后过期

        # 获取勾选信息，如果开启则为ON
        remember =request.POST.get('remember')
        if remember != "on":
            request.session.set_expiry(0)
            # 没有勾选则设置为退出后失效,
        else:
            request.session.set_expiry(None)
            # 勾选则默认为2周，整数则是N秒后退出
        next = request.GET.get('next')
        # 如果next不为空，则返回到nextx的页面
        if next:
            return redirect(next)
        else:
            return redirect(reverse('goods:index'))

            # 响应请求，返回html界面 (进入首页)



class LogoutView(View):
    """退出登录"""


    def get(self, request):
        """处理退出登录逻辑"""

        # 由Django用户认证系统完成：会清理cookie
        # 和session,request参数中有user对象
        logout(request)

        # 退出后跳转：由产品经理设计
        return redirect(reverse('goods:index'))


class UserAddressViem(LoginRequiredMixin,View):
    """用户地址"""
    # 参数1 为登陆检测的函数，内置装饰器对函数进行装修，调用自带的login_required方法，判断用户是否已经登录
    # 如果 @login_required 检测到未登录， 可以配置指定要跳转到哪个界面
    def get(self, request):
        """显示地址"""
        try:
            address = Address.objects.filter(user=request.user)\
                .order_by('-create_time')[0]
            # address = request.user.address_set.latest('create_time')
        except Exception:
            address = None

        context = {
            'which_page': 3,
            'address': address,
        }
        return  render(request, 'user_center_site.html', context)

    def post(self, request):
        """"新增一个地址"""

        # 获取用户请求参数
        receiver = request.POST.get('receiver')
        detail= request.POST.get('detail')
        zip_code = request.POST.get('zip_code')
        mobile = request.POST.get('mobile')
        # 判断数据合法 如果为空 返回错误
        if not all([receiver, detail, mobile]):
            return render(request, 'user_center_site.html', {'errmsg': '参数不完整'})
        # 保存地址到数据库中
        Address.objects.create(
            receiver_name=receiver,
            receiver_mobile=mobile,
            detail_addr=detail,
            zip_code=zip_code,
            user=request.user,

        )

        return redirect(reverse('users:address'))


class UserOrderViem(LoginRequiredMixin,View):
    """用户订单"""
    def get(self, request):
        context = {
            'which_page': 2
        }
        return render(request, 'user_center_order.html', context)


class UserInfoView(LoginRequiredMixin,View):
    """用户中心"""
    def get(self, request):


        # todo:从redis中读取登陆用户浏览过的商品，
        # 返回一个StricRedis
        # strict_redis = get_redis_connection("default") #参数默认可以为空
        strict_redis = get_redis_connection()  # type:strict_redis
        # 读取所以的商品id，返回一个列表
        key = 'history_%s' % request.user.id
        sku_ids = strict_redis.lrange(key, 0, 4)
        print(sku_ids)
        # 根据商品id，查询出商品对象,
        # 设一个空列表 把浏览记录按照表的顺便加到skus表中并显示
        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=int(sku_id))
            skus.append(sku)

        try:
            address = request.user.address_set.latest('create_time')
        except Exception:
            address = None

        context = {
            'which_page': 1,
            'address': address,
            'skus': skus,
        }
        return render(request, 'user_center_info.html', context)