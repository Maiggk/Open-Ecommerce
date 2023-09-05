from django.urls import URLPattern
from django.urls import path
from .views import (
    remove_from_cart,
    reduce_quantity_item,
    add_to_cart,
    ProductView,
    HomeView,
    OrderSummaryView,
    CheckoutView,
    PaymentView,
    SuccessPaymentView,
    ProfileUserView,
    getDetailOrder,
    renderPDF
)

app_name = 'nucleo'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),# Pagina Base
    path('category=<str:filter>', HomeView.as_view(), name='home_category'),# Busqueda por categoria de productos
    path('price=<int:minprice>/<int:maxprice>', HomeView.as_view(), name='home_price'), # Filtrado por precio
    path('search/', HomeView.as_view(), name='home_search'), # Busqueda de productos
    path('producto/<pk>/', ProductView.as_view(), name='producto'),
    path('add-to-cart/<pk>/<int:qty>/',add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<pk>/',remove_from_cart, name='remove-from-cart'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('reduce-quantity-item/<pk>/', reduce_quantity_item, name='reduce-quantity-item'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/', PaymentView.as_view(),name='payment'),
    path('payment_success/<key_order>/<session_id>/<payment_type>', SuccessPaymentView.as_view(),name='payment_success'),
    path('profile-user/', ProfileUserView.as_view(),name='profile-user'),
    path('detail-oder/<or_id>', getDetailOrder,name='order-detail'),
    path('pdf-detail/<order_key>', renderPDF,name='pdf-detail'),
]