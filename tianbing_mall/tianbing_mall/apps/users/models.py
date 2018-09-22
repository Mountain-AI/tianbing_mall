from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from itsdangerous import TimedJSONWebSignatureSerializer

from users import constants


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

    # 最后配置!!!
        # 在django中,定义完模型后第一次迁移需要配置文件设置AUTH_USER_MODEL='users.User'
        # 中间省略了models,是因为添加了导包路径;

    def generate_verify_email_url(self):
        """
        生成邮箱验证链接:针对用户专有url,利用isdangerous
        self:即是当前用户模型
        :return: 返回url
        """
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        # 嵌入用户数据,一个就行,两个更好
        data = {"user_id": self.id, "email": self.email}
        # 将当前用户的数据data转成字典后序列化,
        # 为何要再进行转换
        token = serializer.dumps(data).decode()

        # 拼接url
        verify_url = "http://www.tianbing.site:8080/success_verify_email.html/?token=" + token
        return verify_url









