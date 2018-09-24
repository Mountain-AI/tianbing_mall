from areas.models import Area
from rest_framework import serializers


class AreaSerializer(serializers.ModelSerializer):
    """
    为顶级行政区划提供数据列表:即不出去关系字段parent,其关联名是subs
    """
    class Meta:
        model = Area
        fields = ("id", "name")


class SubAreaSerializer(serializers.ModelSerializer):
    """
    提供区域详细地址:序列化带有自关联名字为subs的字段,且对subs进行再次序列化
    """
    # 注意:如果设置了many=True,就必须设置read_only或者write_only
    subs = AreaSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ("id", "name", "subs")