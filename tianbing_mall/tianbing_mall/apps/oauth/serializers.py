from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from oauth.models import OAuthQQUser
from oauth.utils import OAuthQQ
from users.models import User


class OAuthQQUserSerializer(serializers.ModelSerializer):
    """
    继承ModelSerializer:应为很多字段用的User模型类
    """
    # 自定义User模型没有的字段
    # mobile字段重写,直接正则校验手机号码格式
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    access_token = serializers.CharField(label='操作凭证', write_only=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        # 映射用于校验的字段:一部分用户序列化,一部分用于反序列化;通过read_only与write_only区分
        fields = ('mobile', 'password', 'sms_code', 'access_token', 'id', 'username', 'token')
        # 额外的选项参数
        extra_kwargs = {

            'username': {
                "read_only": True
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

    def validate(self, data):
        """

        :param data:
        :return:
        """
        # 1.校验access_token
        access_token = data["access_token"]
        # 调用自定义的方法使用isdangerous校验access_token获取其中的openid
        openid = OAuthQQ.check_bind_user_access_token(access_token)

        if not openid:
            raise serializers.ValidationError("无效的access_token")
        # 如果校验access_token成功,向数据中添加新的元素openid用于创建用户时存数据库
        data["openid"] = openid

        # 2.校验短信
        # 连接
        redis_conn = get_redis_connection('verify_codes')
        # 取出前端发送的短信
        sms_code = data["sms_code"]
        # 获取redis中存储的真正的短信
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        # 对比
        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        # 3.如果用户存在,检查用户密码,最后将user对象返回:用于创建时签发JWT token
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = data["password"]
            if not user.check_password(password):
                raise serializers.ValidationError("密码错误")
            # 密码校验成功,data中添加元素user
            data["user"] = user
        # 校验方法最后都将数据返回
        return data

    def create(self, validated_data):
        """
        重写保存用户的方法:
            user不存在则需要保存到两张表User和OAuthQQUser
            user存在则将user保存在三方关系表OAuthQQUser
        """
        print("绑定用户validated_data:", validated_data)
        openid = validated_data["openid"]
        mobile = validated_data["mobile"]
        password = validated_data["password"]
        user = validated_data.get("user")  # user有可能不存在

        # 创建用户的三种方式:下面这两种创建后需set_password加密
        # user = super().create(validated_data)
        # user = User.objects.create(**validated_data)
        if not user:
            # 用户不存在则直接创建:第三种创建方式,直接传字段对应的值,将自动set_password加密
            user = User.objects.create_user(
                username=mobile, mobile=mobile, password=password)
        # 用户存在了之后将其添加进与QQ的三方关系表
        OAuthQQUser.objects.create(user=user, openid=openid)

        # 使用JWT给用户签发token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 给user对象添加token属性值
        user.token = token

        # 新增:返回新建的用户前,给视图添加user,用于视图post方法内:当调用父类的post方法之后,在进行合并购物车,能获取到user
        self.context["view"].user = user

        # 返回用户后,当序列化时,使用的是返回后的user的数据
        return user















