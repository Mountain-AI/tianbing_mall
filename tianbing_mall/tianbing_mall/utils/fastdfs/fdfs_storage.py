from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from fdfs_client.client import Fdfs_client


# 自定义文件存储系统:继承django的Storage
@deconstructible
class FastDFSStorage(Storage):
    """
    实现可以使用FastDFS存储文件的存储类:以下方法是必须实现的
    """
    def __init__(self, base_url=None, client_conf=None):
        """
        进行初始化:添加默认参数值
        :param base_url:用于构造图片完整路径,图片服务器使用的域名
        :param client_conf:FastDFS客户端配置文件的路径
        """
        # 初始化时必须支持默认值
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    def _open(self, name, mode="rb"):
        """仅仅用来保存文件,因此用不到打开,但又必须实现此方法,直接pass即可"""
        pass

    def _save(self, name, content):
        """
        在FastDFS中保存文件的方法:返回内容用于存储到数据库
        :param name: 传入的文件名
        :param content: 文件对象
        :return: 将保存到数据库中的FastDFS的文件名返回
        """
        # 实例化一个Fdfs客户端对象,同时传递使用的配置
        client = Fdfs_client(self.client_conf)
        # 接收上传文件的结果:ret保存的是一个字典
        # 上传文件:filename:本地要有这个文件;buffer:本地可没有的远程上传过来的
        ret = client.upload_by_buffer(content.read())
        # 抛出异常
        if ret.get("Status") != "Upload successed.":
            raise Exception("upload file failed")

        # 仅仅将file_id返回,当用的时候在拼接上base_url
        file_name = ret.get("Remote file_id")

        return file_name

    def url(self, name):
        """
        用于返回文件的完整url路径:当通过image.url调用
        :param name: 数据库中保存的文件名
        :return: 完整的url
        """
        return self.base_url + name

    def exists(self, name):
        """
        用于判断文件是否存在:FastDFS可以自行解决文件的重名问题
        但是:此处返回False,为了告诉Django上传的文件都是新的,随便上传
        :param name: 文件名
        :return: 返回false即是上传的额文件名都不存在,可以上传
        """
        return False



