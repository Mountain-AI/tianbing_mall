from django.contrib import admin

# Register your models here.

from . import models

# Register your models here.

# 注册广告内容的模型类
admin.site.register(models.ContentCategory)
admin.site.register(models.Content)























