from collections import OrderedDict

from goods.models import GoodsChannel


def get_categories():
    """获取商品分类菜单并返回分类的字典信息"""
    categories = OrderedDict()
    channels = GoodsChannel.objects.order_by("group_id", "sequence")

    for channel in channels:
        # 当前组
        group_id = channel.group_id
        if group_id not in categories:
            categories[group_id] = {"channels": [], "sub_cats": []}
        # 当前频道的类别
        cat1 = channel.category
        # 追加当前频道:????
        categories[group_id]["channels"].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url,
        })
        # 构建当前类别的子类别
        for cat2 in cat1.goodscategory_set.all():
            cat2.sub_cats = []
            # goodscategory_set??
            for cat3 in cat2.goodscategory_set.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]["sub_cats"].append(cat2)

    return categories


























