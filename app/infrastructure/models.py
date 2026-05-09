from uuid import UUID
from uuid6 import uuid7
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PSU_UUID


class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str
    password_hash: str

class CustomerRead(SQLModel):
    id: UUID
    name: str

class CustomerLogin(SQLModel):
    name: str
    password: str

class Seller(SQLModel, table=True):
    __tablename__ = "sellers"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str
    legal_name: Optional[str] = None
    inn: str
    kpp: Optional[str] = None
    password_hash: str
    
    products: List["Product"] = Relationship(back_populates="seller")

class Category(SQLModel, table=True):
    __tablename__ = "categories"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str
    slug: str = Field(unique=True, index=True)
    description: Optional[str] = None
    parent_id: Optional[UUID] = Field(default=None, foreign_key="categories.id")
    image_url: Optional[str] = None
    is_active: bool = Field(default=True)
    
    # SEO поля
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    meta_tags: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    parent: Optional["Category"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Category.id"},
        back_populates="children"
    )
    children: List["Category"] = Relationship(back_populates="parent")
    products: List["Product"] = Relationship(back_populates="category")

class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    seller_id: UUID = Field(foreign_key="sellers.id")
    category_id: Optional[UUID] = Field(default=None, foreign_key="categories.id")
    title: str
    slug: str = Field(unique=True, index=True)
    image_url: Optional[str] = None
    description: Optional[str] = None
    status: str = Field(default="CREATED")
    rating: float = Field(default=0.0)
    orders_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    seller: Seller = Relationship(back_populates="products")
    category: Optional[Category] = Relationship(back_populates="products")
    skus: List["SKU"] = Relationship(back_populates="product")

class CharacteristicValue(SQLModel, table=True):
    __tablename__ = "sku_characteristics"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    sku_id: UUID = Field(foreign_key="skus.id")
    name: str
    value: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SKU(SQLModel, table=True):
    __tablename__ = "skus"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    product_id: UUID = Field(foreign_key="products.id")
    seller_id: UUID = Field(foreign_key="sellers.id")
    name: str
    price: int  # В копейках/центах
    old_price: Optional[int] = Field(default=None)
    image_url: Optional[str] = None
    status: str = Field(default="ACTIVE")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    product: Product = Relationship(back_populates="skus")
    characteristics: List[CharacteristicValue] = Relationship()
    stock: Optional["Stock"] = Relationship(back_populates="sku")

class Stock(SQLModel, table=True):
    __tablename__ = "stocks"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    sku_id: UUID = Field(foreign_key="skus.id", unique=True)
    quantity: int = Field(default=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    sku: SKU = Relationship(back_populates="stock")
