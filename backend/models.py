from pydantic import BaseModel
from typing import List, Optional

class OutfitItem(BaseModel):
    category: str  # e.g., "shirt", "jeans", "shoes"
    color: Optional[str] = None
    style: Optional[str] = None

class ProductSearchRequest(BaseModel):
    outfit: List[OutfitItem]

class Product(BaseModel):
    name: str
    price: str
    link: str
    image: Optional[str] = None

class ProductSearchResponse(BaseModel):
    products: List[Product]

