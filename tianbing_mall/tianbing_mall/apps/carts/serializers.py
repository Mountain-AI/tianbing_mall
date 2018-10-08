from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    """
    购物车序列化器:完成前端数据的校验
    """
    sku_id = serializers.IntegerField(label="sku_id", min_value=1)
    count = serializers.IntegerField(label="数量", min_value=1)
    selected = serializers.BooleanField(label="是否勾选", default=True)

    def validate(self, attrs):
        """
        校验:sku_id,count是否正确,最后将数据返回
        """
        # 尝试查询当前sku_id是否存在
        try:
            sku = SKU.objects.get(id=attrs["sku_id"])
        except SKU.DoesNotExist:
            raise serializers.ValidationError("商品不存在")
        # 校验数量是否小于库存
        if attrs["count"] > sku.stock:
            raise serializers.ValidationError("商品库存不足")
        return attrs


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')
    selected = serializers.BooleanField(label='是否勾选')

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')
















