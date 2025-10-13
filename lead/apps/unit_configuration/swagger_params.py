# swagger_params.py
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

# ✅ 通用路径参数：支持 32/36 位 UUID
uuid_path_param = OpenApiParameter(
    name="id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    description="资源 UUID，可为 32 位或 36 位格式"
)

# ✅ BOM 查询参数：按产品或父项过滤
bom_filter_params = [
    OpenApiParameter(
        name="product",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="所属产品 UUID，可为 32 或 36 位"
    ),
    OpenApiParameter(
        name="parent",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="父 BOM 子项 UUID，可为空"
    )
]

# ✅ 分页参数
pagination_params = [
    OpenApiParameter(
        name="limit",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="每页数量（默认 20）"
    ),
    OpenApiParameter(
        name="offset",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="偏移量（从第几条开始）"
    )
]

# ✅ 排序与搜索参数
filter_params = [
    OpenApiParameter(
        name="search",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="模糊搜索关键词"
    ),
    OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="排序字段，如 `-created_at` 表示倒序"
    )
]
