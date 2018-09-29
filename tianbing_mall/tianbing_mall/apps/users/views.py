from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from goods.models import SKU
from users import constants
from . import serializers


# CreateAPIView继承了CreateModelMixin和GenericAPIView,其提供了post方法增加创建
from users.models import User


# url(r'^users/$', views.UserView.as_view()),
class UserView(CreateAPIView):
    """
    用户注册:url(r"^users/$", views.UserView.as_view())
    """
    serializer_class = serializers.CreateUserSerializer


# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
class UsernameCountView(APIView):
    """
    用户名是否唯一处理:仅仅是对当前用户名进行数据库过滤查询,再将count返回,无其他逻辑,因此只需集成APIView
    """
    # url路径传参需要函数接收;url查询字符串用request.query_params接收;request.data中则是对post,put,patch解析之后的(文件和非文件)数据
    def get(self, request, username):
        """
        将前端请求的用户名总数数据返回
        """
        count = User.objects.filter(username=username).count()
        data = {
            "username": username,
            "count": count
        }
        # GET：返回资源对象的列表（数组）
        # POST：返回新生成的资源对象
        # PUT：返回完整的资源对象
        # PATCH：返回完整的资源对象
        # DELETE：返回一个空文档
        return Response(data)


# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class MobileCountView(APIView):
    """
    电话是否唯一处理:相当与判断当前手机号是否已经注册
    """
    def get(self, request, mobile):

        count = User.objects.filter(mobile=mobile).count()
        data = {
            "mobile": mobile,
            "count": count
        }
        return Response(data)


# url(r'^user/$', views.UserDetailView.as_view()),
class UserDetailView(RetrieveAPIView):
    """
    用户的基本信息详情
    RetrieveAPIView提供get方法:
        将数据库的信息序列化后包裹在Response的data中返回
    """
    # 指明自定义的序列化器
    serializer_class = serializers.UserDetailSerializer
    # 指明权限必须登录认证后才能访问:接收列表或元组
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        :return: 返回当前请求的用户:源码中get_object方法是从查询集过滤的单一对象
        """
        # 重点:类视图对象中可以通过类视图对象的属性获取request(View中在dispatch前封装的有)
        #   而django中请求request对象中,user属性表明当前请求的用户
        # 因为请求url中没有用户<pk>,因此可以从当前请求对象中获取当前用户对象
        return self.request.user


# url(r'^email/$', views.EmailView.as_view()),
class EmailView(UpdateAPIView):
    """
    用户邮箱验证并更新:UpdateAPIView中封装的有put方法
    获取emial,校验emial,查询user,更新数据,序列化返回email
    """
    # 指明自定义的序列化器
    serializer_class = serializers.EmailSerializer
    # 指明权限必须登录认证后才能访问:接收列表或元组
    permission_classes = [IsAuthenticated]

    def get_object(self):

        return self.request.user


# url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
class VerifyEmailView(APIView):
    """
    用户从邮件链接跳转至验证邮箱的视图:通过url中查询字符串token进行用户校验
    """
    def get(self, request):
        """
        验证邮箱是一个根据token查询匹配用户的过程,get请求即可
        """
        # 从url查询字符串中获取token
        token = request.query_params.get("token")
        print("用户从邮箱url中跳转到验证链接时在界面created加载之前发送请求通过url传递的token:", token)
        if not token:
            return Response({"message": "缺少token"}, status=status.HTTP_400_BAD_REQUEST)
        # 通过在User模型类自定义的静态方法验证token,验证成功会返回当前用户对象
        user = User.check_verify_email_token(token)
        if user is None:
            # 表明token有问题,可能过期
            return Response({"message": "验证信息无效"}, status=status.HTTP_400_BAD_REQUEST)
        # 如果用户存在,则将用户数据的邮箱激活状态设为True,返回成功
        user.email_active = True
        user.save()
        return Response({"message": "OK"})


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户收货地址的增删改查
    注意:视图集只有使用as_view()方法时,才会将action与对应的请求方式对应上;
        当使用了as_view()方法后
    """
    serializer_class = serializers.UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        修改查询集:显示逻辑删除is_delete=False的结果
        """
        return self.request.user.addresses.filter(is_deleted=False)

    # GET  /address
    def list(self, request, *args, **kwargs):
        """
        用户收货地址列表
        重写list方法,返回数据增加user_id,default_address_id及limit
        """
        queryset = self.get_queryset()
        # 指定序列化器:也可以在get_serializer_class方法中根据动作进行分配
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            # 增加数据库没有的数据
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            # 只有addresses使用序列化器,另外三个自定义
            'addresses': serializer.data,
        })

    # POST /addresses/
    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)
        # 源码:创建成功返回的状态码201
        return super().create(request, *args, **kwargs)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()
        # 删除成功返回的状态码204
        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址:
        """
        # 接收pk在调用get_object时会自动传递进去获取单个对象
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        # 指定使用的序列化器:传递更新标题的对象及接收的前端数据
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserBrowserHistoryView(CreateAPIView):
    """
    用户浏览记录:继承CreateAPIView:post添加浏览记录;
    """
    serializer_class = serializers.AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        查询数据库浏览历史记录:根据redis存的sku_id查询数据库取出sku对象,再进行序列化校验
        :return:将序列化之后的id, name, price, default_image_url, comments用于个人中心显示
        """
        # user_id
        user_id = request.user.id

        # 查询redis, 获取连接对象
        redis_conn = get_redis_connection("history")
        # 重点:根据user_id进行查询sku_id:str和hash取值通过get;list类型通过lrange key start stop
        # 返回的是一个sku_id的数字列表
        sku_id_list = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)
        # 通过从redis查询的sku_id_list遍历查询对象
        # 重点:此处不能使用过滤查询中的范围in,因为用范围查到的结果是无序的,需要挨个遍历
        skus = []
        for sku_id in sku_id_list:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        # 将skus列表中的对象进行序列化返回:即使将对象的属性转换成字典
        serializer = serializers.SKUSerializer(skus, many=True)

        # 将序列化后的数据返回:
        # HttpResponse和Response的区别:DRF提供的Response(其继承自HttpResponse)，提供了渲染器render对数据进行渲染，数据必须是字典;
        # 而HttpResponse不会进行加以渲染，指定content_type即可直接将图片对象返回
        return Response(serializer.data)

























