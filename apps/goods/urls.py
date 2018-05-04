from django.conf.urls import url, include

from apps.goods import views

urlpatterns = [
    url('^index$', views.IndexView.as_view(), name='index'),
    # 127.0.0.1:8000/detail/商品Id
    url('^detail/(\d+)$', views.DetailView.as_view(), name='detail'),

    url('^list/(\d+)/(\d+)$', views.ListView.as_view(), name='list'),
]