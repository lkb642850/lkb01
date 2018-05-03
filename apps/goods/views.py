from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection
from redis import StrictRedis

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods, GoodsSKU


class BaseCartView(View):
    def get_cart_count(self,request):
        cart_count = 0
        if request.user.is_authenticated():
            # 获取 StrictRedis 对象
            strict_redis = get_redis_connection()  # type: StrictRedis
            key = 'cart_%s' % request.user.id
            # 从redis中获取购物车数据，返回字典 获取所有的属性和值： hgetall(key)
            cart_dict = strict_redis.hgetall(key)
            # 遍历购物车字典的值，累加购物车的值
            for c in cart_dict.values():
                cart_count += int(c)

        return cart_count


class IndexView(BaseCartView):
    """进入首页"""
    def get2(self, request):
        return render(request, 'index.html')

    def get(self, request):
        # 读取redis中的缓存数据,index_page_datada是自定义的一个键
        # index_page_data=context字典数据  键=值
        context = cache.get("index_page_data")
        if not context:
            print('没有缓存，从mysql中读取')
            # 查询商品类别数据
            categories = GoodsCategory.objects.all()
            # 查询商品轮播轮数据
            # index为表示显示先后顺序的一个字段，值小的会在前面
            slide_skus = IndexSlideGoods.objects.all().order_by('index')
            # 查询商品促销活动数据
            promotions = IndexPromotion.objects.all().order_by('index')[0:2]

            for c in categories:
                # 查询当前类型所以的文字类型和图片 0代表文字，1 代表图片
                text_skus = IndexCategoryGoods.objects.filter(
                    display_type=0, category=c)
                image_skus = IndexCategoryGoods.objects.filter(
                    display_type=1, category=c)[0:4]
                # 动态给对象新增实例属性
                c.text_skus = text_skus
                c.image_skus = image_skus

            #定义要缓存的数据： 字典
            context = {
                'categories': categories,
                'slide_skus': slide_skus,
                'promotions': promotions,

            }
            # 保存数据到redis 中，参数一 键名 参数 2 要缓存的数据 参数3 时间
            cache.set('index_page_data', context, 60*30)
        else:
            print('使用缓存')

        # 获取用户添加到购物车的数量
        cart_count = self.get_cart_count(request)
        # 给字典新增一个键值
        context['cart_count'] = cart_count
        return render(request, 'index.html', context)


class DetailView(BaseCartView):
    """商品详情界面"""

    def get(self, request, sku_id):

        # 查询商品详情信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 查不到跳转到首页
            return redirect(reverse('goods:index'))
        # 获取所有的类别数据
        categories = GoodsCategory.objects.all()


        return render(request, 'detail.html')