import json
import logging
import urllib
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer, BadData

from oauth import constants
from oauth.exceptions import OAuthQQAPIError

logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    QQ认证辅助工具类
    """
    def __init__(self, client_id=None, redirect_uri=None, state=None, client_secret=None):
        """
        qq认证要求提供的必要参数
        """
        self.client_id = client_id if client_id else settings.QQ_CLIENT_ID
        self.redirect_uri = redirect_uri if redirect_uri else settings.QQ_REDIRECT_URI
        # self.state = state if state else settings.QQ_CLIENT_ID
        self.state = state or settings.QQ_STATE
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET

    def get_qq_login_url(self):
        """
        获取qq登录的网址:通过params用urlencode实现动态的从外界传入参数
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": self.state
        }
        url = "https://graph.qq.com/oauth2.0/authorize?" + urlencode(params)

        return url

    def get_access_token(self, code):
        """
        接收code,根据code请求qq接口,获取access_token进行返回
        """
        # 指定请求的qq端口
        url = "http://graph.qq.com/oauth2.0/token?"
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "client_secret": self.client_secret
        }

        # 将参数params编码成查询字符串格式,并拼接到url
        url += urllib.parse.urlencode(params)
        # 尝试发送请求
        try:
            # 接受请求返回的响应
            resp = urlopen(url)
            # 读取响应
            resp_data = resp.read()  # 读取的是byte类型,需要进行解码
            resp_data = resp_data.decode()

            # 读取内容:access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
            # 解析内容:查询字符串利用urllib的parse_qs方法;
            resp_dict = urllib.parse.parse_qs(resp_data)
        except Exception as e:
            logger.error("获取access_token异常:%s" % e)
            raise OAuthQQAPIError
        else:
            # 从解析结果的字典中获得access_token;
            access_token = resp_dict.get("access_token")
            # 将获取的token返回
            return access_token[0]

    def get_openid(self, access_token):
        """
        接收access_token,根据access_token请求qq接口,获取openid进行返回
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token

        # 尝试请求
        try:
            resp = urlopen(url)
            # 读取响应体
            resp_data = resp.read()  # bytes类型
            resp_data = resp_data.decode()  # 转换成str类型

            # 读取内容:callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            # 解析内容:字典字符串利用切片
            resp_data = resp_data[10:-4]
            # 将切取的字符串转成字典
            resp_dict = json.loads(resp_data)
        except Exception as e:
            logger.error("获取openid异常:%s" % e)
        else:
            openid = resp_dict.get("openid")
            return openid

    def generate_bind_user_access_token(self, openid):
        """
        qq用户经查询不存在时生成假的token返回
        """
        # 使用isdangerous的序列化器:接收2个参数
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        # 固定用法
        token = serializer.dumps({"openid": openid})
        return token.decode()

    @staticmethod
    def check_bind_user_access_token(access_token):
        """
        qq用户存在时校验access_token
        """
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            print(data)
            # access_token中包含openid
            return data["openid"]















