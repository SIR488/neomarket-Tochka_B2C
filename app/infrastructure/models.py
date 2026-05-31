from uuid import UUID
from uuid6 import uuid7
from datetime import datetime, timezone, date
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import JSONB

class Favorite(SQLModel, table=True):
    __tablename__ = 'favorites'
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    customer_id: UUID = Field(foreign_key="customers.id")
    product_id: UUID = Field(foreign_key="products.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

    __table_args__ = (UniqueConstraint('customer_id', 'product_id'),)

class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    email: str = Field(sa_column=UniqueConstraint('email'))
    first_name: str
    last_name: str
    date_of_birth: date
    is_active: bool = Field(default=True)
    password_hash: str
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    addresses: List["Address"] = Relationship(back_populates="customer")

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
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

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
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    
    seller: Seller = Relationship(back_populates="products")
    category: Optional[Category] = Relationship(back_populates="products")
    skus: List["SKU"] = Relationship(back_populates="product")

class CharacteristicValue(SQLModel, table=True):
    __tablename__ = "sku_characteristics"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    sku_id: UUID = Field(foreign_key="skus.id")
    name: str
    value: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

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
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

    product: Product = Relationship(back_populates="skus")
    characteristics: List[CharacteristicValue] = Relationship()
    stock: Optional["Stock"] = Relationship(back_populates="sku")

class Stock(SQLModel, table=True):
    __tablename__ = "stocks"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    sku_id: UUID = Field(foreign_key="skus.id", unique=True)
    quantity: int = Field(default=0)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    sku: SKU = Relationship(back_populates="stock")

class Cart(SQLModel, table=True):
    __tablename__ = 'carts'
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    customer_id: UUID = Field(foreign_key="customers.id", unique=True, index=True)
    
    cart_items: List["CartItem"] = Relationship(
        back_populates="cart",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class CartItem(SQLModel, table=True):
    __tablename__ = 'cart_items'
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    cart_id: UUID = Field(foreign_key="carts.id")
    sku_id: UUID = Field(foreign_key="skus.id")
    quantity: int = Field(default=1, nullable=False)
    unit_price_at_add: Optional[int] = Field(default=None)
    unavailable_reason: Optional[str] = Field(default=None)

    cart: Cart = Relationship(back_populates="cart_items")
    sku: SKU = Relationship()

class Address(SQLModel, table=True):
    __tablename__ = "addresses"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    customer_id: UUID = Field(foreign_key="customers.id", index=True)
    
    country: str = Field(max_length=100)
    region: Optional[str] = Field(default=None, max_length=200)
    city: str = Field(max_length=200)
    street: str = Field(max_length=200)
    building: str = Field(max_length=50)
    apartment: Optional[str] = Field(default=None, max_length=50)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    
    recipient_name: Optional[str] = Field(default=None, max_length=200)
    recipient_phone: Optional[str] = Field(default=None, max_length=20)
    
    comment: Optional[str] = Field(default=None, max_length=500)
    is_default: bool = Field(default=False)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    
    customer: Customer = Relationship(back_populates="addresses")

class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_methods"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    customer_id: UUID = Field(foreign_key="customers.id", index=True)
    provider: str = Field(default="card")
    card_mask: str = Field(default="****")
    is_active: bool = Field(default=True)

class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="customers.id", index=True)
    status: str = Field(default="CREATED", index=True)
    total_amount: int
    address_id: Optional[UUID] = Field(default=None, foreign_key="addresses.id")
    payment_method_id: Optional[UUID] = Field(default=None, foreign_key="payment_methods.id")
    idempotency_key: UUID = Field(unique=True, index=True)
    fulfill_called: bool = Field(default=False)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    
    items: List["OrderItem"] = Relationship(back_populates="order")
    payment_method: Optional["PaymentMethod"] = Relationship()
    address: Optional["Address"] = Relationship()

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id")
    sku_id: UUID
    product_id: UUID
    product_title: str
    sku_name: str
    quantity: int
    unit_price: int
    line_total: int
    
    order: Order = Relationship(back_populates="items")

class B2BEventIdempotency(SQLModel, table=True):
    __tablename__ = "b2b_event_idempotency"
    idempotency_key: UUID = Field(primary_key=True)
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )