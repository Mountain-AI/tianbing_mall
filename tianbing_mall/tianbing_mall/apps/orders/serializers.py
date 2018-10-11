from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers
import logging

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods

logger = logging.getLogger("django")


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器:用于结算序列化器使用
    """

    # 补充模型类没有的i字段
    count = serializers.IntegerField(label="数量", min_value=1)

    class Meta:
        model = SKU
        fields = ("id", "name", "default_image_url", "price", "count")


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    # 定义DecimalField(max_digits=10共计十位,decimal_places=2小数两位)
    freight = serializers.DecimalField(label="运费", max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    保存订单序列化器:反序列校验address和pay_method;序列返回order_id
    """
    class Meta:
        model = OrderInfo
        fields = ("order_id", "address", "pay_method")

        # 声明仅序列化返回的字段
        read_only_fields = ("order_id",)
        # 增加额外参数
        extra_kwargs = {
            "address": {
                "write_only": True,  # 仅反序列化校验;映射中没有require,则默认True
            },
            "pay_method": {
                "write_only": True,  # 仅反序列化校验
                "required": True  # 有默认值,需声明必传字段
            }
        }


    def create(self, validated_data):
        """
        对于反序列化校验之后的字段数据,保存到订单数据表中
        :return: order对象
        """
        # 提取校验后的数据
        address = validated_data["address"]  # 校验之后的address是一个对象
        pay_method = validated_data["pay_method"]

        # 获取用户user,根据用户id生成专有订单号
        user = self.context["request"].user

        # 从redis提取数据:创建连接对象
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

        # 如果购物车数据为空,抛出异常
        if not cart:
            raise serializers.ValidationError("没有需要结算的商品")

        # 如有数据:创建并开启一个事务:完成保存订单和生成order_id
        with transaction.atomic():
            # 创建一个保存点:方便整体回滚或提交操作
            save_point = transaction.savepoint()

            try:

                # 生成订单号:strftime将datetime转为字符串;strptime将str转为datetime
                order_id = timezone.now().strftime("%Y%m%d%H%M%S") + ("%09d" % user.id)

                # 保存订单信息表: OrderInfo新增一条数据,create方法返回创建成功的对象
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,  # 临时设为0,后面再改
                    total_amount=Decimal("0"),  # 临时设为0,后面再改
                    freight=Decimal("10.00"),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM["UNSEND"] if pay_method==OrderInfo.PAY_METHODS_ENUM["CASH"] else OrderInfo.ORDER_STATUS_ENUM["UNPAID"]
                )

                # 查询已勾选的商品对象
                sku_id_list = cart.keys()
                # sku_obj_list = SKU.objects.filter(id__in=sku_id_list)  # 范围查询

                # 遍历需要结算的商品数据
                for sku_id in sku_id_list:

                    while True:
                        # 在循环体内查询当前商品对象
                        sku = SKU.objects.get(id=sku_id)
                        # 购买的商品数量cart={"sku_1": 8,....}
                        sku_count = cart[sku.id]

                        # 并接收初始库存和销量
                        origin__stock = sku.stock
                        origin__sales = sku.sales

                        # 判断库存是否充足
                        if sku.stock < sku_count:
                            # 库存不足,回滚事务到保存点,并抛出异常
                            transaction.savepoint_rollback(save_point)
                            raise serializers.ValidationError("商品%s库存不足" % sku.name)

                        # sku表:库存减去sku_count,销量加sku_count
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()  # 此法容易造成多个用户都能抢到库存只有1件的商品

                        # 使用更新update方法保存新的库存和销量
                        new_stock = origin__stock - sku_count
                        new_sales = origin__sales + sku_count
                        # 增加乐观锁:防止多个用户购买,库存不足却都能下单成功的bug
                        result = SKU.objects.filter(id=sku.id, stock=origin__stock).update(stock=new_stock, sales=new_sales)

                        # update返回受影响的行数
                        if result == 0:
                            # 更新失败,有别的用户已经买掉了一点,则继续尝试查询
                            continue

                        # 保存订单商品信息表: OrderGoods新增一条当前商品数据
                        OrderGoods.objects.create(
                            order=order,  # 即是刚刚创建的订单对象
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                            # 其余字段都有默认值
                        )

                        # 更新订单的count数据
                        order.total_count += sku_count  # 订单总数
                        order.total_amount += (sku_count * sku.price)  # 订单总额

                        break

                # 当遍历完毕,此订单order的数据即构造完成,可以保存
                order.total_amount += order.freight
                order.save()

            except serializers.ValidationError:
                # 作用:接收校验错误的异常,不再回滚
                raise
            except Exception as e:
                # 其他异常记录到log并回滚,抛出
                logger.error(e)
                transaction.savepoint_rollback(save_point)
                raise
            else:
                # 成功,从保存点提交
                transaction.savepoint_commit(save_point)

            # 至此订单已经保存成功,接下来删除redis购物车的数据即可
            pl = redis_conn.pipeline()
            # hash:hdel可以删除多个键及其对应的值
            pl.hdel("cart_%s" % user.id, *redis_cart_selected)
            # set:srem可以删除多个值
            pl.srem("cart_selected_%s" % user.id, *redis_cart_selected)

            pl.execute()

            # 将创建的订单order对象返回
            return order




































