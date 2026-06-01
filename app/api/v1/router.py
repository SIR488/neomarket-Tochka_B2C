from fastapi import APIRouter
from app.api.v1.routes import (products, categories, auth, 
                               catalog, favorites, cart, buyer, 
                               addresses, payment_methods)

api_router = APIRouter()
api_router.include_router(products.router, prefix="/products", tags=["product"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(buyer.router, prefix="/buyers/me", tags=["buyer"])
api_router.include_router(addresses.router,prefix="/buyers/me/addresses", tags=["addresses"])
api_router.include_router(payment_methods.router,prefix="/buyers/me/payment-methods", tags=["payment_methods"])