import pickle

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
import base64

from carts import constants
from carts.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer

# /cart/  接收参数:sku_id,count
from goods.models import SKU


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
        serializer = self.get_serializer(data=request.data)
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

            # 返回校验后的数据给前端
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
            # 返回的cookie需要是一条字符串
            cart_cookie_str = cart_cookie_bytes.decode()

            # 设置cookie:构造相应对象
            response = Response(serializer.data)
            # 注意:添加有效期,否则是临时cookie
            response.set_cookie("cart", cart_cookie_str, max_age=constants.CART_COOKIE_EXPIRES)

            # 返回
            return response

    def get(self, request):
        """查询购物车"""
        # 判断用户登录状态
        try:
            user = request.user
        except Exception:
            user = None

        # 查询
        if user and user.is_authenticated:
            # 如果用户已登录，从redis中查询  sku_id  count selected
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            # redis_cart = {
            #     商品的sku_id  bytes字节类型: 数量  bytes字节类型
            #     商品的sku_id  bytes字节类型: 数量  bytes字节类型
            #    ...
            # }

            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            # redis_cart_selected = set(勾选的商品sku_id bytes字节类型, ....)

            # 遍历 redis_cart，形成cart_dict
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_selected
                }
        else:
            # 如果用户未登录，从cookie中查询
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                # 表示cookie中没有购物车数据
                cart_dict = {}

        # cart_dict = {
        #     sku_id_1: {
        #         'count': 10
        #         'selected': True
        #     },
        #     sku_id_2: {
        #         'count': 10
        #         'selected': False
        #     },
        # }

        # 查询数据库
        sku_id_list = cart_dict.keys()
        sku_obj_list = SKU.objects.filter(id__in=sku_id_list)

        # 遍历sku_obj_list 向sku对象中添加count和selected属性
        for sku in sku_obj_list:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 序列化返回
        serializer = CartSKUSerializer(sku_obj_list, many=True)
        return Response(serializer.data)

    def put(self, request):
        """修改购物车"""
        # sku_id, count, selected
        # 校验
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']

        # 判断用户的登录状态
        try:
            user = request.user
        except Exception:
            user = None

        # 保存
        if user and user.is_authenticated:
            # 如果用户已登录，修改redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 处理(更新)数量 hash
            pl.hset('cart_%s' % user.id, sku_id, count)

            # 处理勾选状态 set
            if selected:
                # 表示勾选
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 表示取消勾选, 删除
                pl.srem('cart_selected_%s' % user.id, sku_id)

            pl.execute()
            return Response(serializer.data)

        else:
            # 未登录，修改cookie
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                # 表示cookie中没有购物车数据
                cart_dict = {}
            # cart_dict = {
            #     sku_id_1: {
            #         'count': 10
            #         'selected': True
            #     },
            #     sku_id_2: {
            #         'count': 10
            #         'selected': False
            #     },
            # }

            response = Response(serializer.data)

            if sku_id in cart_dict:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

                cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()

                # 设置cookie
                response.set_cookie('cart', cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)

            return response

    def delete(self, request):
        """删除购物车商品sku_id"""
        # 校验
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 取出校验后的数据
        sku_id = serializer.validated_data["sku_id"]

        # 尝试获取用户登录状态
        try:
            user = request.user
        except Exception:
            user = None

        # 已登录,则从redis中删除
        if user and user.is_authenticated:
            redis_conn = get_redis_connection("cart")
            # 通过管道实例对象进行对此操作
            pl = redis_conn.pipeline()
            # 删除hash
            pl.hdel("cart_%s" % user.id, sku_id)
            # 删除set的勾选状态
            pl.srem("cart_selected_%s" % user.id, sku_id)

            pl.execute()
            # 删除成功进返回204状态码即可
            return Response(status=status.HTTP_204_NO_CONTENT)

        # 未登录,则从cookie中删除
        else:
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                # 表示cookie中没有购物车数据
                cart_dict = {}

            # 先构造响应体
            response = Response(status=status.HTTP_204_NO_CONTENT)

            # 在此id是cart_dict内的请求下在进行删除,不存在则过掉
            if sku_id in cart_dict:
                del cart_dict[sku_id]  # 删除字典中一个键值对

                # 删除成功后通过响应体重新构造cookie
                response.set_cookie("cart", cart_dict, max_age=constants.CART_COOKIE_EXPIRES)

            return response















