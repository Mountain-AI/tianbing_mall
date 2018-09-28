import time
from collections import OrderedDict

import os

from django.conf import settings
from django.template import loader

from contents.models import ContentCategory
from goods.models import GoodsChannel


def generate_static_index_html():
    """
    此函数作用:动态的生成主页静态的html文件
    """
    print("%s: generate_static_index_html" % time.ctime())
    # ???
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

    # 广告内容
    contents = {}
    contents_categories = ContentCategory.objects.all()
    for cat in contents_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by("sequence")

    # 渲染模板
    contex = {
        "categories": categories,
        "contents": contents
    }
    template = loader.get_template("index.html")
    # 渲染好的html字符串数据
    html_text = template.render(contex)
    # 拼接存放生成的静态文件的路径
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, "index.html")
    # 保存
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_text)















