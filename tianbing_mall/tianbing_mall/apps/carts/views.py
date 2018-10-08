import pickle

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
import base64

from carts import constants
from carts.serializers import CartSerializer


# /cart/  接收参数:sku_id,count
class CartView(GenericAPIView):
    """
    购物车视图
    """
    serializer_class = CartSerializer

    def perform_authentication(self, request):
        """重写该视图的身份认证,将其pass掉, 由视图自己进行身份认证"""
        pass

    def post(self, request):
        """
        定义post请求,添加商品(sku_id, count, selected)到购物车
        """
        # 校验:request.data从请求体中取数据
        serializer = self.get_serializer(date=request.data)
        serializer.is_valid(raise_exception=True)

        # 取出校验后的数据进行保存
        sku_id = serializer.validated_data["sku_id"]
        count = serializer.validated_data["count"]
        selected = serializer.validated_data["selected"]

        # 尝试获取用户是否登录:用户区分数据保存位置及redis中区分用户购物车数据
        try:
            # 如果前端headers中不传递凭证,就是一个匿名用户:AnonymousUser,其is_authen..属性为False
            # 如果传递了凭证(如JWT),则使用上面自定义的认证方法进行pass放过
            user = request.user
        except Exception:
            user = None
        # 已登录且认证过(非匿名),则保存到redis
        if user and user.is_authentication:
            # 获取redis连接对象
            redis_conn = get_redis_connection("cart")
            # 多步操作使用pipeline
            pl = redis_conn.pipeline()
            # 保存购物车数据(hash类型:根据user_id为名进行区分,保存sku_id为键,count为值)
            pl.hincrby("cart_%s" % user.id, sku_id, count)  # hincrby累加
            # 保存购物车勾选状态(set类型:根据user_id进行去重保存sku_id)
            if selected:
                # 如果接收的数据有勾选,则保存勾选状态的sku_id
                pl.sadd("cart_selected%s" % user.id, sku_id)
            # 执行pipeline
            pl.execute()

            # 返回校验后的数据给前端:用于显示???
            return Response(serializer.data)

        # 未登录,则保存到浏览器cookie中
        else:
            """
            cart_dict = {
                sku_id_1: {
                    'count': 10,
                    'selected': True
                },
                sku_id_2: {
                    'count': 20,
                    'selected': True
                },
            }
            """
            # 获取cookie,并从中解析出cart_dict
            cart_cookie_str = request.COOKIES.get("cart")

            if cart_cookie_str:
                # 解析
                cart_cookie_bytes = cart_cookie_str.encode()
                cart_cookie_bytes = base64.b64decode(cart_cookie_bytes)  # b64解码
                # pickle
                cart_dict = pickle.loads(cart_cookie_bytes)
            else:
                # 如果购物车没有数据,则设置空字典用于保存
                cart_dict = {}

            # 如果商品sku_id已经在购物车中,则count累加, selected重新赋值
            if sku_id in cart_dict:
                cart_dict[sku_id]["count"] += count
                cart_dict[sku_id]["selected"] = selected
            else:
                # 如果商品sku_id不在购物车中,则在字典中新增
                cart_dict[sku_id] = {
                    "count": count,
                    "selected": selected
                }

            # 将新的cart_dict用pickle转成二进制后加密
            cart_cookie_bytes = base64.b64encode(pickle.dumps(cart_dict))
            # 返回的cookie需要是一条字符串:不应该是encode()???
            cart_cookie_str = cart_cookie_bytes.decode()

            # 设置cookie:构造相应对象
            response = Response(serializer.data)
            # 注意:添加有效期,否则是临时cookie
            response.set_cookie("cart", cart_cookie_str, max_age=constants.CART_COOKIE_EXPIRES)

            # 返回
            return response
























