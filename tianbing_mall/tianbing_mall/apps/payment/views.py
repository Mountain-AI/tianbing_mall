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
from payment.models import Payment


class PaymentView(APIView):
    """发起支付视图"""
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

        # 2,创建AliPay实例
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

        # 3,通过实例进行电脑网站支付,返回一个支付宝支付链接信息
        #   跳转至https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay_client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),  # Decimal类型转为str,防止不识别
            subject="天冰商城%s" % order_id,  # 订单标题
            return_url="http://www.meiduo.site:8080/pay_success.html",
            notify_url=None  # 可选,不填则使用默认值
        )

        # 4,拼接链接返回前端
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return Response({'alipay_url': alipay_url})


# PUT  /payment/status/?支付宝参数
#           参数包括:sign out_trade_no trade_no total_amount seller_id ....
class PaymentStatusView(APIView):
    """
    支付状态视图:修改订单支付状态
    """
    def put(self, request):
        """接收前端发送的支付成功后返回的数据,保存到数据库"""
        # 提取参数
        alipay_request_data = request.query_params  # Query_dict
        if not alipay_request_data:
            return Response({"message": "缺少参数"}, status=status.HTTP_400_BAD_REQUEST)
        # 参数正常,将查询字典转换为普通的字典
        alipay_request_dict = alipay_request_data.dict()
        # 将字典中的sign剔除出来,并根据其进行验证其他参数
        signature = alipay_request_dict.pop("sign")

        # 创建支付实例
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

        # 通过实例进行验证支付宝参数:参照参数sign校验其他参数,返回True或False
        success = alipay_client.verify(alipay_request_dict, signature)
        if success:
            # 支付成功
            order_id = alipay_request_dict.get("out_trade_no")  # 获取前端发送的订单编号
            # 支付宝流水号
            trade_id = alipay_request_dict.get("trade_no")

            # 保存支付信息
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            # 更新订单支付状态信息
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"]).update(status=OrderInfo.ORDER_STATUS_ENUM["UNSEND"])



            # 返回交易流水号
            return Response({"trade_id": trade_id})
        else:
            # 验证失败:返回403禁止状态码
            return Response({"message": "验证失败,非法请求"}, status=status.HTTP_403_FORBIDDEN)






















