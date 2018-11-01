from celery import Celery
# 编写celery异步处理发送短信的主要过程

# 为celery使用django配置文件进行设置:
#       celery与manager一样要同时运行,是不同的系统,也要指定配置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tianbing_mall.settings.dev'


# 1,实例化Celery对象:传入名字
celery_app = Celery("tianbing")

# 2,导入配置文件:config_from_object()
celery_app.config_from_object("celery_tasks.config")

# 3,自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms', "celery_tasks.email", "celery_tasks.html"])


