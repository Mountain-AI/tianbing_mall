from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),
]

# 注册搜索请求的路由
router = DefaultRouter()
router.register("skus/search", views.SKUSearchViewSet, base_name="sku_search")

urlpatterns += router.urls