from django.urls import path, include
from . import views
from .import auth_views
from .auth_views import CookieLoginView, CookieLogoutView
from .payment_views import pay_with_wallet, pay_with_qr, pay_on_counter

urlpatterns = [
    path('', views.home, name="home"),
    
    # drf jwt auth urls
    path('auth/login/', CookieLoginView.as_view(), name='rest_login'),
    path('auth/logout/', CookieLogoutView.as_view(), name='rest_logout'),
    path('auth/', include('dj_rest_auth.registration.urls')),  # Signup
    path('auth/status/', auth_views.AuthStatusView.as_view(), name='auth-status'),
    
    
    path("api/get-profile/", views.get_user_profile, name="get-user-profile"),
    path('api/edit-profile/', views.edit_user_profile, name='edit_profile'),
    path('api/products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('api/categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('api/products/<int:pk>/', views.ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('api/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('api/cart/items/', views.fetch_cart_items, name='fetch-cart-items'),
    path('api/cart/update/', views.cart_update, name='cart_update'),
    path('api/cart/remove/', views.cart_remove, name='cart_remove'),
    path('api/checkout/', views.checkout, name='checkout'),
    
    path('api/orders/', views.user_orders_view, name='user-orders'),
    
    path('api/pay/wallet/', pay_with_wallet),
    path('api/pay/qr/', pay_with_qr),
    path('api/pay/counter/', pay_on_counter),
    
    path('fetch-tables/', views.fetch_tables, name='fetch-tables'),
]
