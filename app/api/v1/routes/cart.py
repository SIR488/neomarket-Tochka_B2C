from fastapi import APIRouter, Depends, HTTPException, Header
from uuid import UUID

from app.application.services.cart_service import CartService
from app.api.v1.schemas.cart import (
    CartItemAddRequest, CartResponse,
    CartValidationResponse, CartValidationIssueType
)
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.dependencies.cart_depends import resolve_cart, get_cart_service

router = APIRouter()

@router.get("/", response_model=CartResponse, status_code=200, summary="Получить корзину")
async def get_cart(
        cart_id: UUID = Depends(resolve_cart),
        service: CartService = Depends(get_cart_service)
):
    cart_response = await service.get_cart(cart_id)

    return cart_response

@router.delete("/", status_code=204, summary="Очистить корзину")
async def clear_cart(
        cart_id: UUID = Depends(resolve_cart),
        service: CartService = Depends(get_cart_service)
):
    return await service.clear_cart(cart_id)

@router.post("/items", response_model=CartResponse, status_code=200, summary="Добавить SKU в корзину")
async def add_cart_item(
        body: CartItemAddRequest,
        cart_id: UUID = Depends(resolve_cart),
        service: CartService = Depends(get_cart_service)
):
    sku, avail, issue_type, msg = await service.check_sku(body.sku_id, body.quantity)

    if not sku or issue_type == CartValidationIssueType.PRODUCT_BLOCKED:
        raise HTTPException(status_code=409, detail=msg)

    if issue_type in (CartValidationIssueType.OUT_OF_STOCK, CartValidationIssueType.QUANTITY_REDUCED):
        raise HTTPException(status_code=404, detail=msg or "SKU не найден")

    cart_response = await service.add_item(cart_id, sku.id, body.quantity, sku.price)

    if cart_response in None:
        raise HTTPException(status_code=400)

    return cart_response

@router.patch("/items/{sku_id}", response_model=CartResponse, status_code=200, summary="Изменить количество SKU в корзине")
async def update_cart_item(
        sku_id: UUID,
        body: dict,
        cart_id: UUID = Depends(resolve_cart),
        service: CartService = Depends(get_cart_service)
):
    quantity = body.get("quantity")

    if not quantity or quantity < 1:
        raise HTTPException(status_code=400, detail="quantity должно быть >= 1")

    sku, _, issue_type, msg = await service.check_sku(sku_id, quantity)
    if not sku or issue_type:
        raise HTTPException(status_code=409 if issue_type else 404, detail=msg or "SKU не найден")

    cart_response = await service.update_item(cart_id, sku.id, quantity)
    if not cart_response:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    return cart_response

@router.delete("/items/{sku_id}", response_model=CartResponse, status_code=200, summary="Удалить SKU из корзины")
async def remove_cart_item(
        sku_id: UUID,
        cart_id: UUID = Depends(resolve_cart),
        service: CartService = Depends(get_cart_service)
):
    cart_response = await service.remove_item(cart_id, sku_id)

    if not cart_response:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    return cart_response

@router.post("/validate", response_model=CartValidationResponse, status_code=200, summary="Валидировать корзину перед чекаутом")
async def validate_cart(
        cart_id: UUID = Depends(resolve_cart),
        service: CartService = Depends(get_cart_service)
):
    validation_response = await service.validate_cart(cart_id)

    if not validation_response:
        raise HTTPException(status_code=404, detail="корзина не найдена")

    return validation_response

@router.post("/merge", response_model=CartResponse, status_code=200, summary=" Явное слияние гостевой корзины с пользовательской")
async def merge_cart_endpoint(
    session_id: UUID = Header(alias="X-Session-Id"),
    customer_id: UUID = Depends(get_current_customer),
    service: CartService = Depends(get_cart_service)
):
    cart_response = await service.merge_guest_cart(customer_id, session_id)

    return cart_response