from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    """用户模型:继承django封装好的abstractuser抽象用户类,再次基础上增加mobile字段"""
    # 定义表字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    # 补充邮箱是否激活字段:实现个人中心
    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")

    # 定义表信息
    class Meta:
        db_table = "tb_users"  # 表名
        verbose_name = "用户"
        verbose_name_plural = verbose_name  # plural复数

    # 配置!!!
        # 在django中,定义完模型后第一次迁移需要配置文件设置AUTH_USER_MODEL='users.User'
        # 中间省略了models,是因为添加了导包路径;why?
