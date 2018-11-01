from django.db import models

# Create your models here.


class Area(models.Model):
    """
    行政区划:城市三级联动,用户为添加用户地址信息提供数据
    """
    name = models.CharField(max_length=20, verbose_name="名称", )
    # django中设置外键,自关联用self表示自身,而不是模型类名;on_delete设置为空;
    #   related_name相当与flask的backref,返回一个查询对象列表
    parent = models.ForeignKey('self', on_delete=models.SET_NULL,
                               related_name='subs', null=True, blank=True,
                               verbose_name='上级行政区划')

    class Meta:
        db_table = "tb_areas"
        verbose_name = "行政区划"
        verbose_name_plural = verbose_name

    def __str__(self):
        """"""
        return self.name























