from haystack import indexes

from goods.models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    """
    sku索引数据模型类,作用:
        1,明确搜索引擎中索引数据包含的字段,即是通过那些字段的数据来检索
        2,在前端查询的关键词即是索引类中的字段名
    继承:
        使用haystack中的indexes提供的模型和字段
        Indexable声明可以被索引
    """
    # document=True指明:关键字查询的字段,该字段的索引值可以由多个数据库模型类字段组成;
    # use_template=True指明:哪些模型类字段，后续通过模板来指明
    text = indexes.CharField(document=True, use_template=True)
    # :默认查找路径:templates/search/indexes/goods/sku_text.txt

    # 其他字段通过model_attr指明:引用数据库模型类的特定字段,用于返回给前端
    id = indexes.IntegerField(model_attr="id")
    name = indexes.CharField(model_attr="name")
    price = indexes.DecimalField(model_attr="price")
    default_image_url = indexes.CharField(model_attr="default_image_url")
    comments = indexes.IntegerField(model_attr="comments")

    def get_model(self):
        """
        返回建立索引的模型类:则在模板中使用的就是这个模型类的数据
        """
        return SKU

    def index_queryset(self, using=None):
        """
        :param using:
        返回建立索引的数据查询集
        """
        return self.get_model().objects.filter(is_launched=True)
