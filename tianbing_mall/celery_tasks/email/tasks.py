from django.conf import settings
from django.core.mail import send_mail

from celery_tasks.main import celery_app


@celery_app.task(name="send_active_email")
def send_active_email(to_email, verify_url):
    """
    使用django提供的send_mail方法接收4个参数:
        标题subject,文本内容message,谁发from_email,发谁recipient_list(列表),网页内容html_message(可无)
    """
    subject = "天冰商城邮箱验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用天冰商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    
    # django提供的邮件发送方法send_mail
    send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)

















