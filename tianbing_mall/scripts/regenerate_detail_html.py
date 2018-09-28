#!/usr/bin/env python


"""
脚本功能:手动生成所有SKU的静态detail html文件
"""

import sys

# 增加导包路径
sys.path.insert(0, "../")

# 默认使用当前项目的django配置
import os
if not os.getenv("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "tianbing_mall.settings.dev"

# 让django初始化配置
import django
django.setup()

# 定义任务
from django.template import loader
from django.conf import settings

from goods.utils import get_categories
from goods.models import SKU


def generate_static_sku_detail_html(sku_id):
    """
    异步任务:生成静态商品详情页面
    """
    # 商品分类菜单:自定义生成商品分类方法
    categories = get_categories()

    # 获取当前sku信息
    sku = SKU.objects.get(id=sku_id)
    # 关联查询
    sku.images = sku.skuimage_set.all()

    # 面包屑导航信息中的频道
    goods = sku.goods
    goods.channel = goods.category1.goodschannel_set.all()

    # 构建当前商品的规格链接
    # sku_key = [规格1参数id, 规格2参数id, ....]
    sku_specs = sku.skuspecification_set.order_by("spec_id")
    sku_key = []
    for spec in sku_specs:
        # ???
        sku_key.append(spec.option.id)

    # 获取当前商品的所有sku
    skus = goods.sku_set.all()

    # 构建不同规格参数的sku字典
    # spec_sku_map = {
    #     (规格1参数id, 规格2参数id, 规格3参数id, ...): sku_id,
    #     ...
    # }
    spec_sku_map = {}
    for s in skus:
        # 获取sku规格参数
        s_specs = s.skuspecification_set.order_by("spec_id")
        # 用于形成规格参数-sku字典的键
        key = []
        for spec in s_specs:
            # ????
            key.append(spec.option.id)
        # 向规格参数-sku字典添加记录
        spec_sku_map[tuple(key)] = s.id

    # 获取当前商品的规格信息
    """
    specs = [
       {
           'name': '屏幕尺寸',
           'options': [
               {'value': '13.3寸', 'sku_id': xxx},
               {'value': '15.4寸', 'sku_id': xxx},
           ]
       },
       ...
    ]
    """
    specs = goods.goodsspecification_set.order_by('id')
    # 若当前sku的规格信息不完整，则不再继续
    if len(sku_key) < len(specs):
        return
    for index, spec in enumerate(specs):
        # 复制当前sku的规格键
        key = sku_key[:]
        # 该规格的选项
        options = spec.specificationoption_set.all()
        for option in options:
            # 在规格参数sku字典中查找符合当前规格的sku
            key[index] = option.id
            option.sku_id = spec_sku_map.get(tuple(key))

        spec.options = options

    # 渲染模板，生成静态html文件
    context = {
        'categories': categories,
        'goods': goods,
        'specs': specs,
        'sku': sku
    }

    template = loader.get_template('detail.html')
    html_text = template.render(context)
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'goods/'+str(sku_id)+'.html')
    with open(file_path, 'w') as f:
        f.write(html_text)


if __name__ == '__main__':
    skus = SKU.objects.all()
    for sku in skus:
        print(sku.id)
        generate_static_sku_detail_html(sku.id)

















