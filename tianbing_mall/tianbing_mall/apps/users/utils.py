

# 在返回值中增加username和user_id
import re

from django.contrib.auth.backends import ModelBackend

from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据;然后在配置JWT_AUTH中使用此函数,让django知道
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    """根据帐号获取user对象"""
    try:
        if re.match('^1[]3-9]\d{9}$', account):
            # 帐号是手机
            user = User.objects.get(mobile=account)
        else:
            # 帐号是用户名
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义用户名或手机号认证;然后进行配置,告知django使用自定义的认证后端
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 获取当前用户
        user = get_user_by_account(username)
        if user is not None and user.check_password(password):
            return user






