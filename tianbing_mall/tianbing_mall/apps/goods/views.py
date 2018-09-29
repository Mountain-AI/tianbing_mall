from django.shortcuts import render

# Create your views here.
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView


# GET /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
from goods.models import SKU
from users.serializers import SKUSerializer


class SKUListView(ListAPIView):
    """
    SKU商品列表视图:对商品数据进行分页,并实现按照create(默认),price,sales排序
    :return:1,序列器实现:"id", "name", "price", "default_image_url", "comments"
            2,分页时django默认返回:count	next previous results
    """
    serializer_class = SKUSerializer

    # 指定后端过滤器:使用DRF提供的OrderingFilter过滤器
    filter_backends = (OrderingFilter,)
    # 使用OrderFilter则需指明ordering_fields属性可进行排序的字段
    ordering_fields = ("create", "price", "sales")

    def get_queryset(self):
        """这个查询集的结果给谁了??"""
        category_id = self.kwargs["category_id"]
        # category是一个外键,数据表存的是category_id;is_lanched?
        return SKU.objects.filter(category_id=category_id, is_launched=True)























