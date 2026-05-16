from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID

from app.infrastructure.database import get_db
from app.infrastructure.models import Cart, CartItem, SKU
from app.api.v1.schemas.cart import (
    CartItemAddRequest, CartResponse, CartItem,
    CartValidationResponse, CartValidationIssue, CartValidationIssueType
)
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.dependencies.cart_depends import resolve_cart, merge_guest_cart


router = APIRouter()

async def _check_sku(session: AsyncSession, sku_id: UUID, requested_qty: int):
    """Валидация SKU. Возвращает (sku, available_qty, issue_type, message)"""
    res = await session.execute(select(SKU).where(SKU.id == sku_id))
    sku = res.scalar_one_or_none()
    if not sku:
        return None, 0, CartValidationIssueType.PRODUCT_DELETED, "SKU не найден"
    if sku.status != "ACTIVE":
        return sku, 0, CartValidationIssueType.PRODUCT_BLOCKED, "Товар заблокирован"

    stock = sku.stock
    avail = stock.quantity if stock else 0
    if avail == 0:
        return sku, 0, CartValidationIssueType.OUT_OF_STOCK, "Нет в наличии"
    if avail < requested_qty:
        return sku, avail, CartValidationIssueType.QUANTITY_REDUCED, f"Доступно только {avail} шт."

    return sku, avail, None, ""

async def _build_cart_response(session: AsyncSession, cart: Cart) -> CartResponse:
    """Собирает ответ из существующей корзины"""
    items = []
    subtotal = 0
    items_count = 0
    is_valid = True

    for ci in cart.cart_items:
        sku = ci.sku
        avail = sku.stock.quantity if sku.stock else 0
        is_avail = sku.status == "ACTIVE" and avail > 0
        line_total = sku.price * ci.quantity

        if not is_avail or avail < ci.quantity:
            is_valid = False

        items.append(CartItem(
            sku_id=ci.sku_id,
            product_id=sku.product_id,
            name=sku.name,
            quantity=ci.quantity,
            unit_price=sku.price,
            unit_price_at_add=ci.unit_price_at_add or sku.price,
            line_total=line_total,
            available_quantity=avail,
            is_available=is_avail,
            image_url=sku.image_url
        ))
        subtotal += line_total
        items_count += ci.quantity

    return CartResponse(
        id=cart.id,
        items=items,
        items_count=items_count,
        subtotal=subtotal,
        is_valid=is_valid
    )

@router.get("/", response_model=CartResponse, status_code=200)
async def get_cart(
    cart: Cart = Depends(resolve_cart),
    session: AsyncSession = Depends(get_db)
):
    return await _build_cart_response(session, cart)

@router.delete("/", status_code=204)
async def clear_cart(
    cart: Cart = Depends(resolve_cart),
    session: AsyncSession = Depends(get_db)
):
    for item in cart.cart_items:
        await session.delete(item)
    await session.commit()
    return

@router.post("/items", response_model=CartResponse, status_code=200)
async def add_cart_item(
    body: CartItemAddRequest,
    cart: Cart = Depends(resolve_cart),
    session: AsyncSession = Depends(get_db)
):
    sku, avail, issue_type, msg = await _check_sku(session, body.sku_id, body.quantity)
    if not sku or issue_type == CartValidationIssueType.PRODUCT_BLOCKED:
        raise HTTPException(status_code=404, detail=msg or "SKU не найден")
    if issue_type in (CartValidationIssueType.OUT_OF_STOCK, CartValidationIssueType.QUANTITY_REDUCED):
        raise HTTPException(status_code=409, detail=msg)

    await session.flush()

    item_res = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == body.sku_id)
    )
    item = item_res.scalar_one_or_none()

    if item:
        item.quantity += body.quantity
    else:
        item = CartItem(cart_id=cart.id, sku_id=body.sku_id, quantity=body.quantity, unit_price_at_add=sku.price)
        session.add(item)

    await session.commit()
    return await _build_cart_response(session, cart)

@router.patch("/items/{sku_id}", response_model=CartResponse, status_code=200)
async def update_cart_item(
    sku_id: UUID,
    body: dict,
    cart: Cart = Depends(resolve_cart),
    session: AsyncSession = Depends(get_db)
):
    quantity = body.get("quantity")
    if not quantity or quantity < 1:
        raise HTTPException(status_code=400, detail="quantity должно быть >= 1")

    sku, _, issue_type, msg = await _check_sku(session, sku_id, quantity)
    if not sku or issue_type:
        raise HTTPException(status_code=409 if issue_type else 404, detail=msg or "SKU не найден")

    res = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku_id)
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    item.quantity = quantity
    await session.commit()
    return await _build_cart_response(session, cart)

@router.delete("/items/{sku_id}", response_model=CartResponse, status_code=200)
async def remove_cart_item(
    sku_id: UUID,
    cart: Cart = Depends(resolve_cart),
    session: AsyncSession = Depends(get_db)
):
    res = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku_id)
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    await session.delete(item)
    await session.commit()
    return await _build_cart_response(session, cart)

@router.post("/validate", response_model=CartValidationResponse, status_code=200)
async def validate_cart(
    cart: Cart = Depends(resolve_cart),
    session: AsyncSession = Depends(get_db)
):
    issues = []
    items = []
    subtotal = 0
    items_count = 0
    is_valid = True

    for ci in cart.cart_items:
        sku = ci.sku
        stock = sku.stock if sku else None
        avail = stock.quantity if stock else 0

        issue_type = None
        msg = ""
        if not sku:
            issue_type = CartValidationIssueType.PRODUCT_DELETED
            msg = "Товар удалён"
        elif sku.status != "ACTIVE":
            issue_type = CartValidationIssueType.PRODUCT_BLOCKED
            msg = "Товар заблокирован"
        elif avail == 0:
            issue_type = CartValidationIssueType.OUT_OF_STOCK
            msg = "Нет в наличии"
        elif avail < ci.quantity:
            issue_type = CartValidationIssueType.QUANTITY_REDUCED
            msg = f"Доступно только {avail} шт."

        is_avail = sku.status == "ACTIVE" and avail >= ci.quantity if sku else False
        line_total = sku.price * ci.quantity if sku else 0

        if not is_avail:
            is_valid = False
            if issue_type:
                issues.append(CartValidationIssue(
                    sku_id=ci.sku_id,
                    type=issue_type,
                    message=msg,
                    old_value=ci.quantity,
                    new_value=avail
                ))

        items.append(CartItem(
            sku_id=ci.sku_id,
            product_id=sku.product_id if sku else ci.sku_id,
            name=sku.name if sku else "Удалённый товар",
            quantity=ci.quantity,
            unit_price=sku.price if sku else 0,
            unit_price_at_add=ci.unit_price_at_add or (sku.price if sku else 0),
            line_total=line_total,
            available_quantity=avail,
            is_available=is_avail,
            image_url=sku.image_url if sku else None
        ))
        subtotal += line_total
        items_count += ci.quantity

    validated_cart = CartResponse(
        id=cart.id,
        items=items,
        items_count=items_count,
        subtotal=subtotal,
        is_valid=is_valid
    )
    return CartValidationResponse(is_valid=is_valid, cart=validated_cart, issues=issues)

@router.post("/merge", response_model=CartResponse, status_code=200)
async def merge_cart_endpoint(
    session_id: UUID = Header(alias="X-Session-Id"),
    customer_id: UUID = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db)
):
    """Явное слияние гостевой корзины с пользовательской."""
    merged_cart = await merge_guest_cart(session, customer_id, session_id)
    await session.commit()
    
    return await _build_cart_response(session, merged_cart)