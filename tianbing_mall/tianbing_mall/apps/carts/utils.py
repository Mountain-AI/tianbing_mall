import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    登录是合并购物车数据,将cookie中的数据合并到redis
    登录时,cookie中的数据如果存在与redis相同的商品,则应以cookie为准
    :return:
    """
    # 提取cookie中的cart数据
    cookie_cart = request.COOKIES.get("cart")

    if not cookie_cart:
        # 为空直接返回响应
        return response

    # 如果cookie_cart存在数据,则解析出字典
    cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

    # 获取redis中的cart数据:hash和set
    redis_conn = get_redis_connection("cart")
    redis_cart = redis_conn.hgetall("cart_%s" % user.id)

    # 此时提取出来的redis_cart={
    #   sku_id(bytes) :  count(bytes),
    #   sku_id(bytes) :  count(bytes),
    # }
    # redis最终保存的商品数量的hash数据
    cart = {}
    for sku_id, count in redis_cart.items():
        cart[int(sku_id)] = int(count)

    # 记录redis最终操作时,新增勾选的sku_id
    redis_cart_selected_add = []
    # 记录redis最终操作时,取消勾选的sku_id
    redis_cart_selected_remove = []

    # 处理cookie中解析出来的字典:用于最终合并
    # cookie_cart_dict = {
    #     sku_id_1: {
    #         'count': 10
    #         'selected': True
    #     },..}
    for sku_id, count_selected_dict in cookie_cart_dict.items():
        # 处理count:向cart字典中添加值
        cart[sku_id] = count_selected_dict["count"]

        # 处理selected:区分勾选与非勾选分别添加进不同的列表,方便拆包操作
        if count_selected_dict["selected"]:
            # selected=True,即勾选
            redis_cart_selected_add.append(sku_id)
        else:
            redis_cart_selected_remove.append(sku_id)

    # 执行合并:cart数据保存hash类型,hmset时,不能为空(报错)
    if cart:
        pl = redis_conn.pipeline()

        # hash
        pl.hmset("cart_%s" % user.id, cart)
        # set:不能为空
        if redis_cart_selected_remove:
            pl.srem('cart_selected_%s' % user.id, *redis_cart_selected_remove)
        if redis_cart_selected_add:
            pl.srem('cart_selected_%s' % user.id, *redis_cart_selected_add)

        pl.execute()

    # 合并完毕清楚cookie中的cart
    response.delete_cookie("cart")  # flask也是这个方法
    return response

















