from app.infrastructure.models import Cart, CartItem, SKU, Stock, CartItemRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from uuid import UUID
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.schemas.favorite import FavoriteRead
from sqlmodel import select
from sqlalchemy.orm import selectinload

router = APIRouter()

async def validate(
    sku_id: UUID,
    quantity: int,
    session: AsyncSession):
    result = await session.execute(
        select(SKU).where(SKU.id == sku_id)
    )
    sku = result.scalar_one_or_none()
    if not sku:
        return False, "Товара нет"
    if sku.status!="ACTIVE":
        return False, "Товар недоступен"
    stock = sku.stock
    if stock.quantity < quantity:
        return False, "Товара нет в наличии"
    
    return True, ""

@router.post("/items", response_model=CartItemRead, status_code=200)
async def create_cart_item(
    sku_id: UUID,
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)
):
    result = await session.execute(
        select(Cart).where(Cart.customer_id == customer_id)
    )
    cart = result.scalar_one_or_none()    
    result = await session.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.sku_id == sku_id
        )
    )
    existing_cart_item = result.scalar_one_or_none()
    
    if existing_cart_item:
        existing_cart_item.quantity += 1
    else:
        existing_cart_item = CartItem(cart_id=cart.id, sku_id=sku_id)
        session.add(existing_cart_item)
    
    is_valid, message = await validate(sku_id=sku_id, quantity=existing_cart_item.quantity, session=session)
    if not is_valid:
        await session.rollback()
        raise HTTPException(status_code=400, detail=message)
    
    await session.commit()
    await session.refresh(existing_cart_item)
    
    return existing_cart_item
    
@router.get("/", response_model=list[CartItemRead], status_code=200)
async def get_cart_items(
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)
):
    result = await session.execute(
        select(Cart).where(Cart.customer_id == customer_id)
        .options(selectinload(Cart.cart_items))
    )
    cart = result.scalar_one_or_none()

    ans = list()
    for item in cart.cart_items:
        is_valid, message = await validate(sku_id=item.sku_id,quantity=item.quantity, session=session)
        item_read = CartItemRead(sku_id=item.sku_id,quantity=item.quantity)
        if not is_valid:
            item_read.available = False
            item_read.unavailable_reason = message
        ans.append(item_read)

    return ans


@router.delete("/", status_code=204)
async def delete_cart(
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)
):
    result = await session.execute(
        select(Cart).where(Cart.customer_id == customer_id)
        .options(selectinload(Cart.cart_items))
    )
    cart = result.scalar_one_or_none()
    if cart.cart_items:
        for item in cart.cart_items:
            await session.delete(item)
        await session.commit()


@router.get("/items/{item_id}", response_model=CartItemRead, status_code=200)
async def create_cart_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)
):
    result = await session.execute(
        select(CartItem).where(CartItem.id == item_id)
        .options(selectinload(CartItem.cart))
    )
    item=result.scalar_one_or_none()
    if not item or item.cart.customer_id!=customer_id:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    is_valid, message = await validate(sku_id=item.sku_id,quantity=item.quantity, session=session)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    return item
        
@router.put("/items/{item_id}", response_model=CartItemRead, status_code=200)
async def create_cart_item(
    item_id: UUID,
    quantity: int,
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)
):
    result = await session.execute(
        select(CartItem).where(CartItem.id == item_id)
        .options(selectinload(CartItem.cart))
    )
    item=result.scalar_one_or_none()
    if not item or item.cart.customer_id!=customer_id:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    is_valid, message = await validate(sku_id=item.sku_id,quantity=quantity, session=session)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    item.quantity=quantity
    await session.commit()
    await session.refresh(item)

    return item

@router.delete("/items/{item_id}", status_code=200)
async def create_cart_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)
):
    result = await session.execute(
        select(CartItem).where(CartItem.id == item_id)
        .options(selectinload(CartItem.cart))
    )
    item=result.scalar_one_or_none()
    if not item or item.cart.customer_id!=customer_id:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    
    await session.delete(item)
    await session.commit()
    return