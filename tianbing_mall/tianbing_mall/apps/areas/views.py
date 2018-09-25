from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from areas import serializers
from areas.models import Area


# /areas/   {"get":"list"}  返回顶级数据,即parent=None
# /areas/<pk>   {"get":"retrieve"}  返回详情;
# 继承选择:因此同一个请求方式获取多种结果使用视图集
class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """
    个人中心地址:提供行政区划列表和详情信息;
    继承关系:1,CacheResponseMixin是配置的缓存扩展
            2,ReadOnlyModelViewSet实现了retrieve和list方法,继承了:
                RetrieveModelMixin,ListModelMixin,GenericViewSet
    CacheResponseMixin做的事:
            1,给RetrieveModelMixin,ListModelMixin提供的retrieve和list方法添加cache_response装饰器
            2,是对两个方法返回的分页过的数据进行缓存
    """
    # 不需要分页时进行关闭分页处理
    pagination_class = None

    def get_queryset(self):
        """
        根据url中定义的请求行为选择查询集
        :return: 一个是不含有parent字段过滤对象集合;一个是所有的查询对象
        """
        if self.action == "list":
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """
        根据action选择序列化器
        """
        if self.action == "list":
            return serializers.AreaSerializer
        else:
            return serializers.SubAreaSerializer









