import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from celery_tasks.email.tasks import send_active_email
from .models import User


class CreateUserSerializer(serializers.ModelSerializer):
    """
    创建用户序列化器
    """
    # 自定义User模型没有的字段
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)

    # 增加用于返回给前端序列化的token字段
    token = serializers.CharField(label="JWT token", read_only=True)

    class Meta:
        model = User
        # 映射用于校验的字段:一部分用户序列化,一部分用于反序列化;通过read_only与write_only区分
        #
        fields = ('id',  # DRF知道其是后端产生的
                  'password',  # password需要补充额外选项:read_only,不能返回给前端
                  'username', 'mobile',  # 这两个序列和反序列都需要,不需要增加额外选项
                  'password2', 'sms_code',  'allow',  # 这三个自定义的只在反序列验证用,前端不需要接收
                  'token'
                  )
        # 增加额外的选项参数
        extra_kwargs = {

            'username': {
                # 增加额外选项定义最大和最小长度
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    # 定义验证方法
    def validate_mobile(self, value):
        """验证手机号:唯一性不用校验,但手机格式需要校验"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码是都相同
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        # 连接
        redis_conn = get_redis_connection('verify_codes')
        # 取值
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        # 对比
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        重写保存用户的方法:增加密码加密之后再保存
        密码加密的两种途径:
            1,创建对象,通过对象的set_password(validated_data["password"]),在对象.save()
            2,
        """
        # 删除模型类不存在的属性:也可用pop
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # print("用户登录validated_data:", validated_data)

        # 两者写法的区别在于:
        #   调用不同:一个是数据库原生管理类,一个是父类CreateModelMixin;
        #   参数不同:一个要求多值参数,一个要求是字典
        # user = super().create(validated_data)
        user = User.objects.create(**validated_data)

        # 调用django用户的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 使用JWT给用户签发token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 给user对象添加token属性值
        user.token = token

        # 返回用户后,当序列化时,使用的是返回后的user的数据
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户基本信息序列化器:
    只需序列化返回部分信息,无需在添加别的验证方法
    """
    class Meta:
        model = User
        # 都是read_only???
        fields = ("id", "username", "mobile", "email", "email_active")


class EmailSerializer(serializers.ModelSerializer):
    """
    邮箱验证序列化器:
    校验并返回邮箱;ModelSerializer中封装的有update方法,重写update方法,添加发送邮件的逻辑
    """
    class Meta:
        model = User
        # 继续要序列又需要反序列
        fields = ("id", "email")

    def update(self, instance, validated_data):
        """
        更新邮箱
        :param instance: 当前视图get_object时传递的request.user对象
        :return: 最后将instance对象返回
        """
        # 从验证后的数据中获取参数
        email = validated_data["email"]
        # 将email保存到数据库
        instance.email = email
        instance.save()

        # 生成当前用户专有的验证链接:使用isdangerous根据user对象生成token
        # 每个用户都有可能验证邮箱,直接在模型类中定义generate_verify_email_url方法
        url = instance.generate_verify_email_url()

        # 发送激活验证邮件
        send_active_email.delay(email, url)
        return instance















