from django.contrib import admin

# Register your models here.

from . import models


class SKUAdmin(admin.ModelAdmin):
    """
    自定义站点SKU管理器类:继承自ModelAdmin
    """
    def save_model(self, request, obj, form, change):
        obj.save()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        # 发布任务:生成静态html并传入sku_id
        generate_static_sku_detail_html.delay(obj.id)


class SKUSpecificationAdmin(admin.ModelAdmin):
    """
    sku规格:specification规格;special特殊,especial特别的
    """
    def save_model(self, request, obj, form, change):
        obj.save()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


class SKUImageAdmin(admin.ModelAdmin):
    """
    sku_image图片管理器
    """
    def save_model(self, request, obj, form, change):
        # obj即是sku_image模型类对象
        obj.save()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

        # 设置SKU模型类的默认图片字段
        # 获取sku_image模型类的关联对象sku模型
        sku = obj.sku
        # 没有默认图片时才设置
        if not sku.default_image_url:
            # 进行设置:
            # obj.image拿到ImageField字段属性,其内有url属性:ImageField触发文件存储系统
            # image.url即是调用自定义的django的文件储存系统类FastDFSStorage的url方法,返回完整的url路径
            sku.default_image_url = obj.image.url
            sku.save()

    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


# 将自定义的管理器注册到admin站点
admin.site.register(models.GoodsCategory)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
admin.site.register(models.SKUImage, SKUImageAdmin)