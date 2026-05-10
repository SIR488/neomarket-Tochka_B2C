from sqladmin import Admin, ModelView
from app.infrastructure.models import Category, Product, SKU, Stock, Seller, Customer, CharacteristicValue

# Настраиваем отображение каждой модели
class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.slug, Category.is_active]
    column_searchable_list = [Category.name, Category.slug]
    column_filters = [Category.is_active]
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-list"

class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.title, Product.status, Product.category]
    column_searchable_list = [Product.title, Product.slug]
    column_filters = [Product.status, Product.category_id]
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-cart-shopping"

class SKUAdmin(ModelView, model=SKU):
    column_list = [SKU.id, SKU.name, SKU.price, SKU.status]
    column_searchable_list = [SKU.name]
    column_filters = [SKU.status]
    name = "SKU (Вариация)"
    name_plural = "SKU (Вариации)"
    icon = "fa-solid fa-tags"

class StockAdmin(ModelView, model=Stock):
    column_list = [Stock.sku, Stock.quantity, Stock.updated_at]
    name = "Склад"
    name_plural = "Склады"
    icon = "fa-solid fa-box"

class SellerAdmin(ModelView, model=Seller):
    column_list = [Seller.id, Seller.name, Seller.inn]
    column_searchable_list = [Seller.name, Seller.inn]
    name = "Продавец"
    name_plural = "Продавцы"
    icon = "fa-solid fa-shop"

class CustomerAdmin(ModelView, model=Customer):
    column_list = [Customer.id, Customer.name]
    name = "Покупатель"
    name_plural = "Покупатели"
    icon = "fa-solid fa-user"

class CharAdmin(ModelView, model=CharacteristicValue):
    column_list = [CharacteristicValue.name, CharacteristicValue.value, CharacteristicValue.sku_id]
    column_searchable_list = [CharacteristicValue.name, CharacteristicValue.value]
    name = "Характеристика"
    name_plural = "Характеристики"
    icon = "fa-solid fa-sliders"

def setup_admin(app, engine):
    admin = Admin(app, engine)
    # Регистрируем все виды
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(SKUAdmin)
    admin.add_view(StockAdmin)
    admin.add_view(CharAdmin)
    admin.add_view(SellerAdmin)
    admin.add_view(CustomerAdmin)