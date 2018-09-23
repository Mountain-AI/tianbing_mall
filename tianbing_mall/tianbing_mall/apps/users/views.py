from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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









