import logging

from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers

# 获取在配置文件中定义的logger
logger = logging.getLogger('django')


class CheckImageCodeSerializer(serializers.Serializer):
    """
    校验图片验证码序列化器
    """
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):  # attrs是字段和值保存的字典
        """
        校验图片验证码是否正确；还有一种方法是validate_text(self):是对单个字段校验;此处对所有字段
        """
        # 1,取参
        image_code_id = attrs["image_code_id"]
        text = attrs["text"]

        # 2,取已保存的值
        # 获取redis连接对象
        redis_conn = get_redis_connection("verify_codes")
        # 读取当前
        real_image_code = redis_conn.get("img_%s" % image_code_id)

        # 3,判断是否有已保存的值
        if real_image_code is None:
            # 图片验证码不存在或者过期:抛出400异常
            raise serializers.ValidationError("无效的图片验证码")

        # 4,验证存在后进行删除验证码:防止用于对同一验证码多次请求
        # 排除异常,仅仅做删除处理,不在exception中返回500
        try:
            redis_conn.delete("img_%s" % image_code_id)
        except RedisError as e:
            logger.error(e)

        # 5,对比
        # 编码转换:python3中redis返回的值是byte类型
        real_image_code = real_image_code.decode()
        if real_image_code.lower() != text.lower():
            raise serializers.ValidationError("图片验证码错误")

        # 6,验证当前手机号60秒内是否发送过短信
        # 6.1,类试图指定序列化器的时候会默认补充context字典,包含request/format/view分别对应:请求对象/格式/类试图
        # 6.2,url路径传参mobile保存在:类试图view的属性kwargs中
        mobile = self.context["view"].kwargs["mobile"]
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        # 判断是否发送过短信
        if send_flag:
            raise serializers.ValidationError("请求验证码过于频繁")

        # 7,验证完毕将数据返回
        return attrs

