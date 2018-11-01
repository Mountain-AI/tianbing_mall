from areas.models import Area
from rest_framework import serializers


class AreaSerializer(serializers.ModelSerializer):
    """
    为list方法提供省份列表数据:关联字段在数据生成的字段名是parent_id,此序列不需要处理此字段
    """
    class Meta:
        model = Area
        fields = ("id", "name")


class SubAreaSerializer(serializers.ModelSerializer):
    """
    为retrieve方法提供市/区详细地址
    """
    # 注意:如果设置了many=True,就须设置read_only或者write_only
    subs = AreaSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ("id", "name", "subs")
        
        
        
        
        
