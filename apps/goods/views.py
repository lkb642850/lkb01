from django.http.response import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods


class IndexView(View):
    """进入首页"""
    def get2(self, request):
        return render(request, 'index.html')

    def get(self, request):
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

        context = {
            'categories': categories,
            'slide_skus': slide_skus,
            'promotions': promotions,

        }
        return render(request, 'index.html', context)