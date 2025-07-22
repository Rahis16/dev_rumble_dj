# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from django.db.models import Q
import csv
from .models import Order, OrderItem, Payment, Product, Table, InventoryItem, Product, Wallet, UserProfile, Role, Permission
from .serializers import OrderSerializer2, ProductSerializerAdmin
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.paginator import Paginator
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, F
from django.utils.timezone import now
from datetime import timedelta, datetime
from django.utils.timesince import timesince
from .admin_serializers import SimpleUserSerializer, UserProfileSerializer, RoleSerializer, InventoryItemSerializer, RoleSerializerCreateView, PermissionSerializerAddRoleView
from rest_framework import generics, filters
from django.db import models
from .admin_role_serializers import UserStatusSerializer
from django.utils.encoding import smart_str




User = get_user_model()

# just for getting user list 
class UserListAPIViewGetUsers(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = SimpleUserSerializer

#getting the user and userprofile data to use in admin pannel
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_user_profile_data(request, user_id):
    profle_data = get_object_or_404(UserProfile,user__id=user_id)
    serializer = UserProfileSerializer(profle_data, context={'request': request})
    return Response(serializer.data)


#getting user role and details to pre set the current status     
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_user_role_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    profile = getattr(user, 'profile', None)

    return Response({
        "id": user.id,
        "username": user.username,
        "statuses": {
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
        "role": {
            "id": profile.role.id if profile and profile.role else None,
            "name": profile.role.name if profile and profile.role else None
        }
    }, status=status.HTTP_200_OK)    
    

#for updateing user status only    
class UpdateUserStatusAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        is_active = request.data.get("is_active")
        is_staff = request.data.get("is_staff")
        is_superuser = request.data.get("is_superuser")

        if user_id is None:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Optional updates (only if provided in request)
        if is_active is not None:
            user.is_active = is_active
        if is_staff is not None:
            user.is_staff = is_staff
        if is_superuser is not None:
            user.is_superuser = is_superuser

        user.save()

        return Response({
            "detail": f"User '{user.username}' status updated successfully.",
            "statuses": {
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        }, status=status.HTTP_200_OK)


#admin role serializers or user role serializers
class UserStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserStatusSerializer(request.user)
        return Response(serializer.data)
    
    
#getting admin dashboard data
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    today = now().date()
    week_ago = today - timedelta(days=6)

    # 🟩 1. Sales Data for Last 7 Days
    orders = Order.objects.filter(ordered_at__date__gte=week_ago)
    sales_by_day = orders.extra({'day': "date(ordered_at)"}).values('day').annotate(
        sales=Sum('total_price'),
        orders=Count('id')
    ).order_by('day')

    salesData = [
        {
            'name': datetime.strptime(data['day'], '%Y-%m-%d').strftime('%a'),  # Convert str to date
            'sales': float(data['sales']),
            'orders': data['orders']
        }
        for data in sales_by_day
    ]

    # 🟩 2. Menu Items Data (Top 5 Selling Products)
    menu_items = OrderItem.objects.values(name=F('product__name')).annotate(
        value=Sum('quantity')
    ).order_by('-value')[:5]

    colors = ["#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"]
    menuItemsData = []
    for i, item in enumerate(menu_items):
        menuItemsData.append({
            'name': item['name'],
            'value': item['value'],
            'color': colors[i % len(colors)]
        })

    # 🟩 3. Hourly Orders (Today)
    hourly_orders = orders.filter(ordered_at__date=today).extra({
        'hour': "strftime('%%H', ordered_at)"
    }).values('hour').annotate(
        orders=Count('id')
    ).order_by('hour')

    hourlyOrdersData = [
        {
            'hour': f"{int(row['hour']) % 12 or 12}{'AM' if int(row['hour']) < 12 else 'PM'}",
            'orders': row['orders']
        } for row in hourly_orders
    ]

    # 🟩 4. Monthly Revenue
    payments = Payment.objects.all()
    monthly = payments.extra({'month': "strftime('%%m', paid_at)"}).values('month').annotate(
        revenue=Sum('amount')
    ).order_by('month')

    monthlyRevenueData = [
        {
            'month': now().replace(month=int(row['month'])).strftime('%b'),
            'revenue': float(row['revenue']),
            'target': float(row['revenue']) + 10000
        } for row in monthly
    ]

    # 🟩 5. Top Stats Cards
    total_orders = Order.objects.count()
    total_sales = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    active_users = User.objects.filter(is_active=True).count()
    avg_order_value = Order.objects.aggregate(avg=Avg('total_price'))['avg'] or 0
    total_tables = Table.objects.count()
    occupied_tables = Table.objects.filter(status='occupied').count()

    topStatsCards = {
        "total_orders": total_orders,
        "total_sales": float(total_sales),
        "active_tables": f"{occupied_tables}/{total_tables}",
        "active_users": active_users,
        "avg_order_value": round(float(avg_order_value), 2),
    }

    # 🟩 6. Quick Metrics
    orders_in_queue = Order.objects.filter(status='pending').count()
    stock_alerts = InventoryItem.objects.filter(warning_level__in=['Low', 'Critical']).count()
    peak_hour = max(hourlyOrdersData, key=lambda x: x['orders'])['hour'] if hourlyOrdersData else "N/A"

    quickMetrics = {
        "orders_in_queue": orders_in_queue,
        "stock_alerts": stock_alerts,
        "peak_hour": peak_hour
    }
    
    recent_orders = Order.objects.select_related("user").prefetch_related("items", "items__product").order_by("-ordered_at")[:5]
    recentOrdersData = []
    for order in recent_orders:
        item_name = order.items.first().product.name if order.items.exists() else "N/A"
        recentOrdersData.append({
            "id": f"#{order.pk}",
            "item": item_name,
            "time": timesince(order.ordered_at) + " ago",
            "status": order.status.title(),
            "amount": f"Rs. {order.total_price}",
        })
    
    alert_items = InventoryItem.objects.all().order_by("warning_level")[:5]
    inventoryAlertsData = [
        {
            "item": i.item_name,
            "stock": f"{i.quantity} {i.unit}",
            "level": i.warning_level,
            "color": (
                "red" if i.warning_level in ["Low", "Critical"]
                else "yellow" if i.warning_level == "Medium"
                else "green"
            )
        } for i in alert_items
    ]
    
    # Call the class method directly from the model, not from the queryset
    top_delivery_staff = UserProfile.top_by_order_type('delivered')
    top_confirmed_staff = UserProfile.top_by_order_type('confirmed')
    top_preparing_staff = UserProfile.top_by_order_type('prepared')
    top_cancelled_staff = UserProfile.top_by_order_type('cancelled')
    top_refunded_staff = UserProfile.top_by_order_type('refunded')
    
    # Build separate lists or a grouped dictionary
    staff_profiles = {
        "delivered": [
            {"name": staff.user.profile.full_name, "order_count": staff.order_count, "role": staff.user.profile.role.name}
            for staff in top_delivery_staff
        ],
        "confirmed": [
            {"name": staff.user.profile.full_name, "order_count": staff.order_count, "role": staff.user.profile.role.name}
            for staff in top_confirmed_staff
        ],
        "prepared": [
            {"name": staff.user.profile.full_name, "order_count": staff.order_count, "role": staff.user.profile.role.name}
            for staff in top_preparing_staff
        ],
        "cancelled": [
            {"name": staff.user.profile.full_name, "order_count": staff.order_count, "role": staff.user.profile.role.name}
            for staff in top_cancelled_staff
        ],
        "refunded": [
            {"name": staff.user.profile.full_name, "order_count": staff.order_count, "role": staff.user.profile.role.name}
            for staff in top_refunded_staff
        ],
    }


    return Response({
        "salesData": salesData,
        "menuItemsData": menuItemsData,
        "hourlyOrdersData": hourlyOrdersData,
        "monthlyRevenueData": monthlyRevenueData,
        "topStatsCards": topStatsCards,
        "quickMetrics": quickMetrics,
        "recentOrdersData": recentOrdersData,
        "inventoryAlertsData": inventoryAlertsData,
        "staff_profiles": staff_profiles
    })



@api_view(['GET'])
@permission_classes([IsAdminUser])
def fetch_all_orders(request):
    status_filter = request.GET.get('status')

    start_date_param = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    start_date = parse_date(start_date_param) if start_date_param else None
    end_date = parse_date(end_date_param) if end_date_param else None
    search = request.GET.get('search')

    orders = Order.objects.prefetch_related('items', 'items__product', 'table', 'user').all()
    
    if search:
        orders = orders.filter(
            Q(user__username__icontains=search) |
            Q(id__icontains=search)
        )

    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
    else:
        orders = orders.filter(status__in=['pending', 'confirmed', 'preparing', 'cancelled', 'delivered'])
    if start_date and end_date:
        orders = orders.filter(ordered_at__date__range=(start_date, end_date))

    orders = orders.order_by('-ordered_at')

    # Export to CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)

        writer.writerow(['Order ID', 'User', 'Status', 'Total Price', 'Ordered At', 'Table'])
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username,
                order.status,
                order.total_price,
                order.ordered_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.table.number if order.table else 'N/A'
            ])

        return response

    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 5
    paginated_orders = paginator.paginate_queryset(orders, request)

    serializer = OrderSerializer2(paginated_orders, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def fetch_single_order(request, order_id):
    try:
        order = Order.objects.prefetch_related('items', 'items__product', 'table', 'user').select_related('payment').get(pk=order_id)
        serializer = OrderSerializer2(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    
    
#post view for changing payment status
@api_view(['POST'])
@permission_classes([IsAdminUser])  # or your custom is_manager_or_admin
def update_payment_status(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        payment = order.payment

        status_update = request.data.get("status")

        if status_update not in ["pending", "paid", "fake", "failed", "refunded"]:
            return Response({"error": "Invalid payment status"}, status=status.HTTP_400_BAD_REQUEST)
        
        #update wallet if the status is refunded if paid via wallet
        
        if payment.method == "wallet":
            if status_update == "refunded":
                wallet = order.user.wallet
                wallet.balance += order.total_price
                wallet.save()
                
        payment.status = status_update
        payment.save()

        return Response({"message": "Payment status updated successfully"}, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    except Payment.DoesNotExist:
        return Response({"error": "Payment details not found for this order"}, status=status.HTTP_404_NOT_FOUND)
    
    
    
#changing order status to confirmed or cancelled    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    try:
        user = request.user
        user_role = getattr(user.profile.role, 'name', None).lower()

        if not user_role:
            return Response({"error": "User role not found."}, status=status.HTTP_403_FORBIDDEN)

        order = Order.objects.get(pk=order_id)
        new_status = request.data.get("status")

        # List of allowed statuses from model
        allowed_statuses = [choice[0] for choice in Order.STATUS_CHOICES]

        if new_status not in allowed_statuses:
            return Response({"error": f"Invalid status. Allowed: {allowed_statuses}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Role-based allowed transitions
        role_permissions = {
            'admin': allowed_statuses,
            'manager': allowed_statuses,
            'chef': ['preparing', 'cancelled'],
            'server': ['delivered'],
            'cashier': ['cancelled', 'refunded']
        }

        if new_status not in role_permissions.get(user_role, []):
            return Response({"error": f"Role '{user_role}' cannot change status to '{new_status}'."},
                            status=status.HTTP_403_FORBIDDEN)

        # Optional: prevent updates on terminal states
        if order.status in ['cancelled', 'refunded']:
            return Response({"error": f"Order is already {order.status} and cannot be changed."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Set optional audit fields
        if new_status == "confirmed":
            order.confirmed_by = user
        elif new_status == "cancelled":
            order.cancelled_by = user
        elif new_status == "delivered":
            order.delivered_by = user
        elif new_status == "preparing":
            order.prepared_by = user
             # 🔽 Get duration from request and set it
            duration = request.data.get("prepare_duration")
            if not duration:
                return Response({"error": "Prepare duration is required when setting to 'preparing'."},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                duration = int(duration)
                order.prepare_duration = duration
            except ValueError:
                return Response({"error": "Prepare duration must be a valid integer."},
                                status=status.HTTP_400_BAD_REQUEST)
                
        elif new_status == "refunded":
            order.refunded_by = user
        
        
        order.status = new_status
        order.save()

        return Response({
            "message": f"Order status updated to '{new_status}'.",
            "status": order.status,
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
    
    
    
#CRU on products and categories
class AdminProductListCreateView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        # ✅ Filter by is_active if query param exists
        is_active = request.query_params.get('is_active')
        products = Product.objects.all().order_by('-created_at')
        if is_active is not None:
            products = products.filter(is_active=is_active.lower() == 'true')
            
        # ✅ Search by name
        search_query = request.query_params.get('search')
        if search_query:
            products = products.filter(Q(name__icontains=search_query))

        # ✅ Manual pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        paginator = Paginator(products, limit)

        current_page = paginator.page(page)
        serializer = ProductSerializerAdmin(current_page.object_list, many=True, context={'request': request})

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'results': serializer.data
        })

    def post(self, request):
        serializer = ProductSerializerAdmin(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class AdminProductRetrieveUpdateView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializerAdmin(product, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializerAdmin(product, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    


class UserListAPIView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.select_related('user', 'role').all()

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        role = self.request.query_params.get('role')
        search = self.request.query_params.get('search')

        if status and status != "all":
            queryset = queryset.filter(status=status)

        if role and role != "all":
            queryset = queryset.filter(role__name=role)

        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )

        return queryset
    
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # ✅ Handle CSV export
        if request.query_params.get('export') == 'csv':
            return self.export_csv(queryset)

        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 4)

        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            return Response({"error": "Invalid pagination parameters"}, status=status.HTTP_400_BAD_REQUEST)

        paginator = Paginator(queryset, limit)

        try:
            users_page = paginator.page(page)
        except PageNotAnInteger:
            users_page = paginator.page(1)
        except EmptyPage:
            return Response({"error": "Page out of range"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(users_page.object_list, many=True)

        return Response({
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "results": serializer.data,
        })
    
    def export_csv(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="user_profiles.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Username", "Email", "Full Name", "Role", "Status", "Phone", "Faculty", "Program", "Semester", "Orders Count", "Total Spent"
        ])

        for profile in queryset:
            writer.writerow([
                smart_str(profile.user.username),
                smart_str(profile.user.email),
                smart_str(profile.full_name or ""),
                smart_str(profile.role.name if profile.role else ""),
                smart_str(profile.status),
                smart_str(profile.phone_number or ""),
                smart_str(profile.faculty or ""),
                smart_str(profile.program or ""),
                smart_str(profile.semester or ""),
                smart_str(profile.orders_count or ""),
                smart_str(profile.total_spent or ""),
            ])

        return response    


class RoleListAPIView(generics.ListAPIView):
    serializer_class = RoleSerializer
    queryset = Role.objects.prefetch_related('permissions', 'users')
    
    
    
class RoleListCreateAPIView(generics.ListCreateAPIView):
    queryset = Role.objects.prefetch_related('permissions').all()
    serializer_class = RoleSerializerCreateView

class PermissionListAPIView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializerAddRoleView   
    

class AvailableRolesAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        all_choices = dict(Role.ROLE_NAME_CHOICES)
        used_roles = Role.objects.values_list('name', flat=True)
        available = [
            {"value": key, "label": val}
            for key, val in all_choices.items()
            if key not in used_roles
        ]
        return Response(available)    
    
    
class RoleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.prefetch_related('permissions').all()
    serializer_class = RoleSerializerCreateView
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Prevent deletion of critical roles
        if instance.name in ['admin', 'manager', 'customer']:
            return Response(
                {"detail": f"Cannot delete the '{instance.name}' role. It is protected."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch the fallback role (customer)
        fallback_role = get_object_or_404(Role, name='customer')

        # Ensure fallback role has `use_client_panel` permission
        permission_code = 'use_client_panel'
        fallback_permission, created = Permission.objects.get_or_create(
            code=permission_code,
            defaults={'label': 'Use Client Panel'}
        )
        fallback_role.permissions.add(fallback_permission)

        # Reassign users to fallback role
        users_with_role = UserProfile.objects.filter(role=instance)
        reassigned_users = []
        for user in users_with_role:
            user.role = fallback_role
            user.save()
            reassigned_users.append({
                "id": user.id,
                "username": user.username,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "role": {
                    "id": fallback_role.id,
                    "name": fallback_role.name,
                }
            })

        self.perform_destroy(instance)
        return Response({
            "detail": f"Role '{instance.name}' deleted and reassigned to fallback role '{fallback_role.name}'.",
            "reassigned_users": reassigned_users
        }, status=status.HTTP_200_OK)



class AssignUserRoleAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        role_id = request.data.get("role_id")

        if not user_id or not role_id:
            return Response({"detail": "User ID and Role ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Now assign via the profile
        try:
            user.profile.role = role
            if role.name != 'customer':
                
                user.is_staff = True
                print(f"Setting is_staff to {user.is_staff} for user {user.username}")
            else:
                user.is_staff = False
            user.save()   
            print(f"Saving user {user.username} with role {role.name} with is_staff {user.is_staff}") 
            user.profile.save()
            
        except Exception as e:
            return Response({"detail": f"Failed to assign role: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "detail": f"{user.username} has been assigned the role '{role.name}' successfully."
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
def user_stats(request):
    total_users = UserProfile.objects.count()
    active = UserProfile.objects.filter(status='active').count()
    inactive = UserProfile.objects.filter(status='inactive').count()
    staff_user = UserProfile.objects.filter(user__is_staff=True).count()
    revenue = UserProfile.objects.aggregate(total=models.Sum('total_spent'))['total'] or 0

    return Response({
        "total_users": total_users,
        "active_users": active,
        "inactive_users": inactive,
        "staff_users": staff_user,
        "total_revenue": revenue
    })    
    
    
    
# List + Create for Inventory management
class InventoryItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = InventoryItem.objects.all().order_by('-last_updated')
    serializer_class = InventoryItemSerializer



# Retrieve + Update + Delete
class InventoryItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer    
    
    
class InventoryItemListView(generics.ListAPIView):
    serializer_class = InventoryItemSerializer

    def get_queryset(self):
        queryset = InventoryItem.objects.filter(is_deleted=False).order_by("-last_updated")
        warning_level = self.request.query_params.get("warning_level")
        search = self.request.query_params.get("search")

        if warning_level and warning_level.lower() != "all":
            queryset = queryset.filter(warning_level__iexact=warning_level)

        if search:
            queryset = queryset.filter(Q(item_name__icontains=search))

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.query_params.get("export") == "csv":
            return self.export_csv(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def export_csv(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventory.csv"'

        writer = csv.writer(response)
        writer.writerow(["Item Name", "Quantity", "Unit", "Warning Level", "Last Updated"])

        for item in queryset:
            writer.writerow([
                smart_str(item.item_name),
                smart_str(item.quantity),
                smart_str(item.unit),
                smart_str(item.warning_level),
                smart_str(item.last_updated.strftime("%Y-%m-%d %H:%M")),
            ])

        return response    