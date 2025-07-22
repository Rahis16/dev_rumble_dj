from django.urls import path, include
from . import views
from .import auth_views
from .auth_views import CookieLoginView, CookieLogoutView
from .payment_views import pay_with_wallet, pay_with_qr, pay_on_counter, PaymentListAPIView
from . import admin_views 
from . import table_admin_views

urlpatterns = [
    path('', views.home, name="home"),
    
    # drf jwt auth urls
    path('auth/login/', CookieLoginView.as_view(), name='rest_login'),
    path('auth/logout/', CookieLogoutView.as_view(), name='rest_logout'),
    path('auth/', include('dj_rest_auth.registration.urls')),  # Signup
    path('auth/status/', auth_views.AuthStatusView.as_view(), name='auth-status'),
    path('token/refresh/', auth_views.RefreshTokenView.as_view(), name='token-refresh'),


    path("api/get-profile/", views.get_user_profile, name="get-user-profile"),
    path("api/get-wallet/", views.fetch_wallet, name="get-user-wallet"),
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
    path('api/payments/', PaymentListAPIView.as_view(), name='payment-list'),
    
    path('fetch-tables/', views.fetch_tables, name='fetch-tables'),
    
    
    path('api/dashboard/', admin_views.dashboard_data, name='dashboard-data'),
    path('api/admin/orders/', admin_views.fetch_all_orders, name='fetch_all_orders'),
    path('api/admin/orders/<int:order_id>/', admin_views.fetch_single_order, name='fetch_single_order'),
    path('api/admin/orders/<int:order_id>/update-payment-status/', admin_views.update_payment_status, name='update_payment_status'),
    path('api/admin/orders/<int:order_id>/update-status/', admin_views.update_order_status, name='update_order_status'),
    path('api/admin/products/', admin_views.AdminProductListCreateView.as_view(), name='admin-product-list-create'),
    path('api/admin/products/<int:pk>/', admin_views.AdminProductRetrieveUpdateView.as_view(), name='admin-product-detail-update'),
    path('api/users/', admin_views.UserListAPIView.as_view(), name='user-list'),
    path('api/roles/', admin_views.RoleListAPIView.as_view(), name='role-list'),
    path('api/user-stats/', admin_views.user_stats, name='user-stats'),
    path('api/roles-post/', admin_views.RoleListCreateAPIView.as_view(), name='role-list-create'),
    path('api/permissions/', admin_views.PermissionListAPIView.as_view(), name='permission-list'),
    path('api/available-roles/', admin_views.AvailableRolesAPIView.as_view()),
    path('api/user/role-check/', admin_views.UserStatusAPIView.as_view(), name='user-status'),
    path('api/roles/<int:id>/', admin_views.RoleRetrieveUpdateDestroyAPIView.as_view(), name='role-edit-delete'),
    path("api/assign-role/", admin_views.AssignUserRoleAPIView.as_view(), name="assign-user-role"),
    path("api/get-users/", admin_views.UserListAPIViewGetUsers.as_view(), name="assign-user-role"),
    path("api/update-user-status/", admin_views.UpdateUserStatusAPIView.as_view(), name="update-user-status"), #updating status like is_active, is_staff etc
    path('api/user-status-role/<int:user_id>/', admin_views.get_user_role_status, name='user-status-role'), #getting the role of the user and thier status 
    path('api/user-profile-data/<int:user_id>/', admin_views.get_user_profile_data, name='user-profile-data'), #getting the user profile data by id
    
    path('api/tables/', table_admin_views.TableListAPIView.as_view(), name='table-list'),
    path('api/tables/<int:pk>/', table_admin_views.TableStatusUpdateAPIView.as_view(), name='table-status-update'),
    path('api/reservations/', table_admin_views.ReservationListAPIView.as_view(), name='reservation-list'),
    path('api/reservations/create/', table_admin_views.ReservationCreateAPIView.as_view(), name='reservation-create'),
    path('api/reservations/<int:pk>/', table_admin_views.ReservationUpdateDeleteAPIView.as_view(), name='reservation-update-delete'),
    path('api/table-update-logs/', table_admin_views.TableUpdateLogListAPIView.as_view(), name='update-log-list'),
    path("api/inventory-items/", admin_views.InventoryItemListView.as_view(), name="inventory-list-create"),
    path("api/inventory-items/<int:pk>/", admin_views.InventoryItemRetrieveUpdateDestroyAPIView.as_view(), name="inventory-detail"),
]
     