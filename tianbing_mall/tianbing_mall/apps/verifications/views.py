import logging
import random

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

# 自己的包与系统包空一行
from tianbing_mall.libs.captcha.captcha import captcha
from tianbing_mall.utils.yuntongxun.sms import CCP
from verifications import constants
from verifications.serializers import CheckImageCodeSerializer
from celery_tasks.sms.tasks import send_sms_code

# 获取日志记录器logger
logger = logging.getLogger('django')


class ImageCodeView(APIView):
    """
    图片验证码:仅仅生成验证码,用不到别的功能只需继承APIView
    """

    def get(self, request, image_code_id):
        """
        生成图片验证码
        """
        text, image = captcha.generate_captcha()
        print("图片验证码:", text)

        # 获取redis连接对象
        redis_conn = get_redis_connection("verify_codes")
        # 保存验证码
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_EXPIRES, text)
        # 不能使用DRF提供的Response(其继承自HttpResponse),因为Response提供了渲染器render对数据进行渲染,数据必须是字典
        # 而HttpResponse不会进行加以渲染,指定content_type即可直接将图片对象返回
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
        print("短信验证码:", sms_code)

        # 保存短信验证码/发送记录到redis
        redis_conn = get_redis_connection("verify_codes")
        # 给redis管道pipeline添加任务:统一提交
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # 让管道通知redis执行命令
        pl.execute()

        # 3,发送
        # try:
        #     ccp = CCP()
        #     time = str(constants.SMS_CODE_EXPIRES // 60)  # 使用云通讯设置的发送短信的间隔单位:分钟
        #     result = ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error("发送短信[异常][mobile:%s, message:%s]" % (mobile, e))
        #     # 4,构造响应:将数据返回,参数依次是:data(字典),status,template_name,headers,content_type
        #     return Response({"message": "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # else:
        #     if result == 0:
        #         logger.info("发送成功")
        #         return Response({"message": "OK"})
        #     else:
        #         logger.warning("发送短信[失败][mobile:%s]" % mobile)
        #         return Response({"message": "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 使用celery发送短信
        # time = str(constants.SMS_CODE_EXPIRES // 60)
        # send_sms_code.delay(mobile, sms_code, time, constants.SMS_CODE_TEMP_ID)

        return Response({"message": "OK"})











