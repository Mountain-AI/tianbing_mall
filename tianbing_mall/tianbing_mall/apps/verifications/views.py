import random

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from tianbing_mall.libs.captcha.captcha import captcha

from tianbing_mall.libs.yuntongxun.sms import CCP
from verifications import constants
from verifications.serializers import CheckImageCodeSerializer


class ImageCodeView(APIView):
    """
    图片验证码:仅仅生成验证码,用不到别的功能只需继承APIView
    """

    def get(self, request, image_code_id):
        """
        生成图片验证码
        """
        text, image = captcha.generate_captcha()
        # 获取redis连接对象
        redis_conn = get_redis_connection("verify_codes")
        # 保存验证码
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_EXPIRES, text)
        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    """
    发送短信验证码:需要使用序列化器或者别的增加的功能需要继承GenericAPIView
    """
    serializer_class = CheckImageCodeSerializer

    # url路径传参<mobile>直接在函数中接收/查询参数?保存在request.query_params
    def get(self, request, mobile):
        """
        校验图片验证码及发送频率
        """
        # 获取序列化器对象:序列化
        serializer = self.get_serializer(data=request.query_params)
        # 1,校参:主动抛出异常
        serializer.is_valid(raise_exception=True)

        # 2,生成随机短信验证码并保存
        sms_code = "%06d" % random.randint(0, 999999)
        # 保存短信验证码/发送记录到redis
        redis_conn = get_redis_connection("verify_codes")
        # 将保存redis的任务交给redis管道pipeline统一提交
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % sms_code, constants.SMS_CODE_EXPIRES, sms_code)
        # 通过mobile区分
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 3,发送
        ccp = CCP()
        time = str(constants.SMS_CODE_EXPIRES / 60)  # 使用云通讯设置的发送短信的间隔单位:分钟
        ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)

        # 4,构造响应:将数据返回,参数依次是:data(字典),status,template_name,headers,content_type
        return Response({"message": "OK"})













