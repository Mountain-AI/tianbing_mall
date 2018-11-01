from drf_haystack import serializers
from rest_framework.serializers import ModelSerializer

from goods.models import SKU
from goods.search_indexes import SKUIndex


class SKUSerializer(ModelSerializer):
    """用于序列化模型类数据"""

    class Meta:
        model = SKU
        fields = ("id", "name", "price", "default_image_url", "comments")


class SKUIndexSerializer(serializers.HaystackSerializer):
    """
    sku索引结果数据序列化器:继承drf_haystack提供的serializers
    """
    class Meta:
        # 指定使用的模型索引类
        index_classes = [SKUIndex]
        # 要序列化的索引类中的字段
        fields = ("text", "id", "name", "price", "default_image_url", "comments")







