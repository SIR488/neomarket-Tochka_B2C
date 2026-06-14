from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException

from app.api.v1.schemas.cart import CartResponse, CartItem, CartItemAddRequest, CartValidationIssueType, \
    CartValidationResponse, CartValidationIssue
from app.infrastructure.models import Cart
from app.infrastructure.repositories.sku_repository import SKURepository
from app.infrastructure.repositories.cart_repository import CartRepository
from app.infrastructure.b2b_client import B2BClient, B2BUnavailableError
from uuid6 import uuid7
from app.api.v1.schemas.catalog import ImageRef


class CartService:
    def __init__(self, repository: CartRepository, sku_repo: SKURepository, b2b_client: B2BClient):
        self.repository = repository
        self.sku_repo = sku_repo
        self.b2b_client = b2b_client

    async def check_sku(self, sku_id: UUID, requested_qty: int):
        """Валидация SKU через B2B. Возвращает (sku, available_qty, issue_type, message)"""
        try:
            product_data = await self.b2b_client.get_product_by_sku(sku_id)
        except B2BUnavailableError:
            raise HTTPException(status_code=503, detail="B2B service unavailable")
        
        if not product_data:
            return None, 0, CartValidationIssueType.PRODUCT_DELETED, "SKU не найден"
        
        if not product_data.get("is_active"):
            return None, 0, CartValidationIssueType.PRODUCT_BLOCKED, "Товар заблокирован"
        
        avail = product_data.get("available_quantity", 0)
        price = product_data.get("price", 0)
        
        class TempSku:
            def __init__(self, data):
                self.id = UUID(data["id"])
                self.product_id = UUID(data["product_id"])
                self.name = data["name"]
                self.price = price
                self.status = "ACTIVE" if data.get("is_active") else "BLOCKED"
                self.image_url = data.get("image_url")
                self.stock = type('obj', (object,), {'quantity': avail})()
        
        sku = TempSku(product_data)
        
        if avail == 0:
            return sku, 0, CartValidationIssueType.OUT_OF_STOCK, "Нет в наличии"
        if avail < requested_qty:
            return sku, avail, CartValidationIssueType.QUANTITY_REDUCED, f"Доступно только {avail} шт."
        
        return sku, avail, None, ""

    async def _build_response(self, cart: Cart) -> CartResponse:
        items = []
        subtotal = 0
        items_count = 0
        is_valid = True

        for ci in cart.cart_items:
            sku = ci.sku
            avail = sku.stock.quantity if sku.stock else 0
            is_avail = sku.status == "ACTIVE" and avail > 0 and ci.unavailable_reason is None
            line_total = sku.price * ci.quantity

            if not is_avail or avail < ci.quantity:
                is_valid = False
            else:
                subtotal += line_total

            items_count += ci.quantity

            image = None
            if sku.image_url:
                image = ImageRef(
                    id=uuid7(),
                    url=sku.image_url,
                    alt=sku.name,
                    ordering=0,
                    is_main=True
                )

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
                image=image,
                unavailable_reason=ci.unavailable_reason
            ))

        return CartResponse(
            id=cart.id,
            items=items,
            items_count=items_count,
            subtotal=subtotal,
            is_valid=is_valid
        )

    async def resolve_cart(
            self,
            customer_id: Optional[UUID] = None,
            session_id: Optional[UUID] = None,
    ) -> UUID:
        cart = await self.repository.resolve_cart(customer_id, session_id)
        return cart.id

    async def get_cart(self, cart_id: UUID) -> CartResponse:
        cart = await self.repository.get_by_id(cart_id)
        
        sku_ids = [ci.sku_id for ci in cart.cart_items]
        
        if sku_ids:
            try:
                skus_data = await self.b2b_client.get_skus_by_ids(sku_ids)
            except B2BUnavailableError:
                raise HTTPException(status_code=503, detail="B2B service unavailable")
            
            for ci in cart.cart_items:
                b2b_sku = skus_data.get(str(ci.sku_id))
                if b2b_sku:
                    ci.sku.price = b2b_sku.get("price", ci.sku.price)
                    if ci.sku.stock:
                        ci.sku.stock.quantity = b2b_sku.get("available_quantity", 0)
                    if not b2b_sku.get("is_active", True):
                        ci.unavailable_reason = "PRODUCT_BLOCKED"
        
        return await self._build_response(cart)

    async def clear_cart(self, cart_id: UUID) -> None:
        """Очистить корзину"""
        await self.repository.clear_cart(cart_id)

    async def add_item(self, cart_id: UUID, sku_id: UUID, quantity: int, price: int) -> Optional[CartResponse]:
        await self.repository.add_or_update_item(cart_id, sku_id, quantity, price)

        updated_cart = await self.repository.get_cart_with_items(cart_id)

        if not updated_cart:
            return None

        return await self._build_response(updated_cart)

    async def update_item(self, cart_id, sku_id, quantity: int) -> Optional[CartResponse]:
        item = await self.repository.update_item_quantity(cart_id, sku_id, quantity)
        if not item:
            return None

        updated_cart = await self.repository.get_cart_with_items(cart_id)

        if not updated_cart:
            return None

        return await self._build_response(updated_cart)

    async def remove_item(self, cart_id: UUID, sku_id: UUID) -> Optional[CartResponse]:
        item = await self.repository.remove_item(cart_id, sku_id)
        if not item:
            return None

        updated_cart = await self.repository.get_cart_with_items(cart_id)

        if not updated_cart:
            return None

        return await self._build_response(updated_cart)

    async def validate_cart(self, cart_id: UUID) -> Optional[CartValidationResponse]:
        cart = await self.repository.get_cart_with_items(cart_id)
        if not cart:
            return None

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

            is_avail = sku.status == "ACTIVE" and avail >= ci.quantity and ci.unavailable_reason is None if sku else False
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

            image = None
            if sku and sku.image_url:
                image = ImageRef(
                    id=uuid7(),
                    url=sku.image_url,
                    alt=sku.name if sku else "Unknown",
                    ordering=0,
                    is_main=True
                )

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
                image=image,
                unavailable_reason=ci.unavailable_reason
            ))
            if is_avail:
                subtotal += line_total
                items_count += ci.quantity

        validated_cart = CartResponse(
            id=cart.id,
            items=items,
            items_count=items_count,
            subtotal=subtotal,
            is_valid=is_valid
        )

        return CartValidationResponse(
            is_valid=is_valid,
            cart=validated_cart,
            issues=issues
        )

    async def merge_guest_cart(self, customer_id: UUID, session_id: UUID) -> CartResponse:
        merged_cart = await self.repository.merge_guest_into_user(customer_id, session_id)
        return await self._build_response(merged_cart)