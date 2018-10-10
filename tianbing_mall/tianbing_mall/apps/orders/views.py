from decimal import Decimal
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders.serializers import OrderSettlementSerializer


# orders/settlement/
class OrderSettlementView(APIView):
    """
    订单结算视图
    APIView与GenerateAPIView的区别:
        GenerateAPIView继承自APIView,增加了对列表和详情视图可能用到的通用支持方法
        通用方法如下:get_queryset(self)
                    get_serializer_class(self)
                    get_serializer(self, args, *kwargs)
        详情视图方法如下:get_object(self)
    """
    permission_classes = [IsAuthenticated]  # 认证成功后,视图函数才能获取到user

    def get(self, request):
        """获取订单结算页面,返回相关数据"""

        # 获取用户user,需要通过user.id从redis中取出购物车数据
        user = request.user

        # 从redis提取数据:先创建连接对象
        redis_conn = get_redis_connection("cart")
        # hash: count商品数量
        redis_cart_dict = redis_conn.hgetall("cart_%s" % user.id)
        # set: selected勾选商品sku_id
        redis_cart_selected = redis_conn.smembers("cart_selected_%s" % user.id)

        # 对提取出来的数据进行处理:
        # 1,整合hash和set数据,查询数据库获取所有的set已勾选的商品对象;
        cart = {}  #
        for sku_id in redis_cart_selected:  # 以勾选的商品sku_id为准
            # redis中获取出来的数据都是bytes类型,储存时int转换方便提取cart.keys
            # 整合:cart = {sku_id : count , ...}
            cart[int(sku_id)] = int(redis_cart_dict[sku_id])

        # 查询已勾选的商品对象
        sku_id_list = cart.keys()
        sku_obj_list = SKU.objects.filter(id__in=sku_id_list)  # 范围查询
        # 给商品对象添加count属性
        for sku in sku_obj_list:
            sku.count = cart[sku.id]

        # 运费
        freight = Decimal("10.00")

        # 2,序列化数据:freight和skus(即sku_obj_list其是多个对象)
        serializer = OrderSettlementSerializer({"freight": freight, "skus": sku_obj_list})

        # 返回序列化后的数据
        return Response(serializer.data)























