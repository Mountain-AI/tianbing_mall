from drf_haystack import serializers

from goods.search_indexes import SKUIndex


class SKUIndexSerializer(serializers.HaystackSerializer):
    """
    sku索引结果数据序列化器:继承drf_haystack提供的serializers
    """
    class Meta:
        # 指定使用的模型索引类
        index_classes = [SKUIndex]
        # 要序列化的索引类中的字段
        fields = ("text", "id", "name", "price", "default_image_url", "comments")







