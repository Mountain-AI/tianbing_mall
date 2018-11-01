from django.db import models


class BaseModel(models.Model):
    """
    为模型类补充字段:增加新建时间和更新时间
    """
    # 仅仅只在新增创建时添加当前时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    # 只是修改时自动添加当前时间
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        # 指明是抽象模型类,用于别的表(QQ/Sina/Github...)继承使用,迁移时就不会产生这个模型类的表
        abstract = True









