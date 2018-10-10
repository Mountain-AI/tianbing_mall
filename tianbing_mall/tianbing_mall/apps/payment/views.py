import os
from alipay import AliPay
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderInfo


# GET /orders/(?P<order_id>\d+)/payment/
class PaymentView(APIView):
    """支付相关视图"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """
        接受路径传参order_id
        获取支付链接,并拼接后返回前端
        """

        # 1,尝试查询订单是否正确
        try:
            order = OrderInfo.objects.get(order_id=order_id,user=request.user,
                                          pay_method=OrderInfo.PAY_METHODS_ENUM["ALIPAY"],
                                          status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"])
        except OrderInfo.DoesNotExist:
            return Response({"message": "订单信息有误"}, status=status.HTTP_400_BAD_REQUEST)

        # 2,构造支付宝支付链接地址:创建AliPay实例,通过实例请求支付宝
        alipay_client = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # 也可以读取出来的字符串放在下面
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 是否是沙箱环境,默认False
        )

        # 3,通过实例alipay_client进行电脑网站支付:将返回一个支付链接字符串
        #   跳转至https://openapi.alipay.com/geteway.do? + order_string
        order_string = alipay_client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="天冰商城%s" % order_id,  # 订单标题
            return_url="http://www.meiduo.site:8080/pay_success.html",
            notify_url=None  # 可选,不填则使用默认值
        )

        # 4,拼接链接返回前端
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return Response({'alipay_url': alipay_url})






















