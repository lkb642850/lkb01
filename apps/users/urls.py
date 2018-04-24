from django.conf.urls import url

from apps.users import views

urlpatterns = [
    url(r"^index$",views.index),
    # url(r'^register$', views.register,name='register'),     # 进入注册界面
    # url(r'^do_register$', views.do_register, name="do_register"),     # 进入注册界面
    url(r'^register$', views.RegisterView.as_view(), name="register"),     # 进入注册界面 返回一个视图函数
    url(r'^active/(.+)$', views.ActiveView.as_view(), name="active"),     # 进入注册界面 返回一个视图函数
    url(r'^login$', views.LoginView.as_view(), name='login'),         # 登录
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),         # 登录

]