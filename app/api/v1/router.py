from fastapi import APIRouter
from app.api.v1.routes import products, categories, auth, catalog, favorites, cart, buyer

api_router = APIRouter()
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(buyer.router, prefix="/buyer/me", tags=["buyer"])
