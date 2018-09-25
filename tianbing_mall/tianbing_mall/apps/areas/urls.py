from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from areas import views

urlpatterns = [

]

# /areas/   {"get":"list"}  返回顶级数据,即parent=None
# /areas/<pk>   {"get":"retrieve"}  返回详情;
# 它的内部如何实现的??
# simplerouter和defaultrouter的区别:defaultrouter继承自simplerouter;比其多提供一个跟路由
router = DefaultRouter()
router.register("areas", views.AreasViewSet, base_name="areas")

urlpatterns += router.urls
