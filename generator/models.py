from pydantic import BaseModel, Field


class ShopInfo(BaseModel):
    shop_name: str = Field(..., description="店铺全称")
    category: str = Field(..., description="菜系或店铺类型")
    avg_price: str = Field(..., description="人均消费（可以包含单位，如'35元'）")
    signature_dishes: list[str] = Field(..., description="招牌菜列表")
    environment: str = Field(..., description="环境特点")
    service_style: str = Field(..., description="服务风格")
    location_vibe: str = Field(..., description="位置氛围")
    address: str = Field("", description="地址（如可用）")


class ReviewError(Exception):
    pass
