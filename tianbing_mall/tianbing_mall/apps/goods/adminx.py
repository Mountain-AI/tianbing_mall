

# Register your models here.

import xadmin
from xadmin import views

from . import models


# xadmin全局配置
class BaseSetting(object):
    """xadmin的基本配置:"""
    enable_themes = True  # 开启主题切换功能
    # use_bootswatch = True


xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "天冰商城运营管理系统"  # 设置站点标题
    site_footer = "天冰商城集团有限公司"  # 设置站点的页脚
    menu_style = "accordion"  # 设置菜单折叠


xadmin.site.register(views.CommAdminView, GlobalSettings)


class SKUAdmin(object):
    """商品xadmin站点管理"""
    model_icon = 'fa fa-gift'  # 图标样式
    list_display = ['id', 'name', 'price', 'stock', 'sales', 'comments']
    search_fields = ['id','name']  # 搜索字段
    list_filter = ['category']  # 过滤器
    list_editable = ['price', 'stock']  # 列表页面可编辑的字段
    show_detail_fields = ['name']  # 可快速查看详情
    show_bookmarks = True  # 书签
    list_export = ['xls', 'csv', 'xml']  # 可导出的格式


class SKUSpecificationAdmin(object):
    def save_models(self):
        # 保存数据对象
        obj = self.new_obj
        obj.save()

        # 补充自定义行为
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

    def delete_model(self):
        # 删除数据对象
        obj = self.obj
        sku_id = obj.sku.id
        obj.delete()

        # 补充自定义行为
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


# 将自定义的管理器注册到Xadmin站点
xadmin.site.register(models.GoodsCategory)
xadmin.site.register(models.GoodsChannel)
xadmin.site.register(models.Goods)
xadmin.site.register(models.Brand)
xadmin.site.register(models.GoodsSpecification)
xadmin.site.register(models.SpecificationOption)
xadmin.site.register(models.SKU, SKUAdmin)
xadmin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
xadmin.site.register(models.SKUImage)


# class SKUAdmin(admin.ModelAdmin):
#     """
#     自定义站点SKU管理器类:继承自ModelAdmin
#     """
#     def save_model(self, request, obj, form, change):
#         obj.save()
#
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         # 发布任务:生成静态html并传入sku_id
#         generate_static_sku_detail_html.delay(obj.id)
#
#
# class SKUSpecificationAdmin(admin.ModelAdmin):
#     """
#     sku规格:specification规格;special特殊,especial特别的
#     """
#     def save_model(self, request, obj, form, change):
#         obj.save()
#
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(obj.sku.id)
#
#     def delete_model(self, request, obj):
#         sku_id = obj.sku.id
#         obj.delete()
#
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(sku_id)
#
#
# class SKUImageAdmin(admin.ModelAdmin):
#     """
#     sku_image图片管理器
#     """
#     def save_model(self, request, obj, form, change):
#         # obj即是sku_image模型类对象
#         obj.save()
#
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(obj.sku.id)
#
#         # 设置SKU模型类的默认图片字段
#         # 获取sku_image模型类的关联对象sku模型
#         sku = obj.sku
#         # 没有默认图片时才设置
#         if not sku.default_image_url:
#             # 进行设置:
#             # obj.image拿到ImageField字段属性,其内有url属性:ImageField触发文件存储系统
#             # image.url即是调用自定义的django的文件储存系统类FastDFSStorage的url方法,返回完整的url路径
#             sku.default_image_url = obj.image.url
#             sku.save()
#
#     def delete_model(self, request, obj):
#         sku_id = obj.sku.id
#         obj.delete()
#
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(sku_id)


# # 将自定义的管理器注册到admin站点
# admin.site.register(models.GoodsCategory)
# admin.site.register(models.GoodsChannel)
# admin.site.register(models.Goods)
# admin.site.register(models.Brand)
# admin.site.register(models.GoodsSpecification)
# admin.site.register(models.SpecificationOption)
# admin.site.register(models.SKU, SKUAdmin)
# admin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
# admin.site.register(models.SKUImage, SKUImageAdmin)