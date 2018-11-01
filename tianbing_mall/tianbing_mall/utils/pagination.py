from rest_framework import pagination


class StandardResultsSetPagination(pagination.PageNumberPagination):
    """
    商品列表试图指定分页类
    定义完之后在配置文件rest_framework指定DEFAULT_PAGINATION_CLASS对应的路径
    """

    # 如果前端没有指明每页条数,则使用默认的page_size
    page_size = 2
    # 前端访问指明的每页数量的参数名
    page_size_query_param = "page_size"
    # 防止非法请求,限制url传入的每页最大值条数
    max_page_size = 20



























