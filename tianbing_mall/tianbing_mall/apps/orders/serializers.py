from rest_framework import serializers

from goods.models import SKU


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





























