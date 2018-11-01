from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from itsdangerous import TimedJSONWebSignatureSerializer, BadData

from tianbing_mall.utils.models import BaseModel
from users import constants


class User(AbstractUser):
    """用户模型:继承django封装好的abstractuser抽象用户类,再次基础上增加mobile字段"""
    # 定义表字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    # 补充邮箱是否激活字段:实现个人中心
    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")

    # 添加默认收获地址:用字符串关联时的写法注意
    default_address = models.ForeignKey("Address", related_name="users", null=True, blank=True, on_delete=models.SET_NULL, verbose_name='默认地址')

    # 定义表信息
    class Meta:
        db_table = "tb_users"  # 表名
        verbose_name = "用户"
        verbose_name_plural = verbose_name  # plural复数

    # 最后配置!!!
        # 在django中,定义完模型后第一次迁移需要配置文件设置AUTH_USER_MODEL='users.User'
        # 中间省略了models,是因为添加了导包路径;

    # 定性为对象方法
    def generate_verify_email_url(self):
        """
        生成邮箱验证链接:针对用户专有url,利用isdangerous
        self:即是当前用户模型
        :return: 返回url
        """
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        # 嵌入用户数据,一个就行,两个更安全
        data = {"user_id": self.id, "email": self.email}
        # 将
        token = serializer.dumps(data).decode()

        # 拼接url
        verify_url = "http://www.tianbing.site:8080/success_verify_email.html?token=" + token
        return verify_url

    # 定性为静态方法:
    @staticmethod
    def check_verify_email_token(token):
        """
        校验验证邮箱的路径传递到视图中的token:包含user_id 和email
        :return: 验证成功则返回user
        """
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        # 尝试将tokee进行解析
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            # 解析成功则动data中获取user_id和email,查询用户数据
            user_id = data["user_id"]
            email = data["email"]
            # 尝试获取用户信息
            try:
                user = User.objects.get(id=user_id, email=email)
            except User.DoesNotExist:
                return None
            else:
                return user


class Address(BaseModel):
    """
    个人中心用户收获地址信息:此是一张三方关系表,在User模型类中default_address字段关联次模型
    """
    # django和flask关于模型类的定义复习
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses",  verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name="地址名称")
    receiver = models.CharField(max_length=20, verbose_name="收货人")

    # 外键指向Areas/models里面的Area，指明外键ForeignKey时，可以使用字符串应用名.模型类名来定义;models文件名怎么不写?
    # related_name相当于反引用,flask中的backref
    province = models.ForeignKey("areas.Area", on_delete=models.PROTECT, related_name="province_addresses", verbose_name="省")
    city = models.ForeignKey("areas.Area", on_delete=models.PROTECT, related_name="city_addresses", verbose_name="市")
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')

    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    # 固定电话电话,允许为空/空白
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        # 查询此模型类对应的表时默认按照这个排序方式
        ordering = ['-update_time']






