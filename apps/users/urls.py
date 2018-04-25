from django.conf.urls import url

from apps.users import views

urlpatterns = [

    # url(r'^register$', views.register,name='register'),     # 进入注册界面
    # url(r'^do_register$', views.do_register, name="do_register"),     # 进入注册界面
    url(r'^register$', views.RegisterView.as_view(), name="register"),     # 进入注册界面 返回一个视图函数
    url(r'^login$', views.LoginView.as_view(), name='login'),         # 登录
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),         # 登出

    url(r'^active/(.+)$', views.ActiveView.as_view(), name="active"), # 激活视图

    url(r'^address$', views.UserAddressViem.as_view(), name='address'),  # 地址页面
    url(r'^orders$', views.UserOrderViem.as_view(), name='orders'),  # 订单页面
    url(r'^$', views.UserInfoView.as_view(), name='info'),  # 个人用户界面
]