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
from .models import Order, OrderItem, Payment, Product, StaffProfile, Table, InventoryItem, Product, Wallet
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


User = get_user_model()

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
    total_staff = StaffProfile.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    avg_order_value = Order.objects.aggregate(avg=Avg('total_price'))['avg'] or 0
    total_tables = Table.objects.count()
    occupied_tables = Table.objects.filter(is_occupied=True).count()

    topStatsCards = {
        "total_orders": total_orders,
        "total_sales": float(total_sales),
        "active_tables": f"{occupied_tables}/{total_tables}",
        "total_staff": total_staff,
        "active_users": active_users,
        "avg_order_value": round(float(avg_order_value), 2),
    }

    # 🟩 6. Quick Metrics
    orders_in_queue = Order.objects.filter(status='pending').count()
    avg_rating = StaffProfile.objects.aggregate(rating=Avg('rating'))['rating'] or 0
    stock_alerts = InventoryItem.objects.filter(warning_level__in=['Low', 'Critical']).count()
    peak_hour = max(hourlyOrdersData, key=lambda x: x['orders'])['hour'] if hourlyOrdersData else "N/A"

    quickMetrics = {
        "orders_in_queue": orders_in_queue,
        "avg_rating": round(avg_rating, 1),
        "stock_alerts": stock_alerts,
        "peak_hour": peak_hour
    }
    
    recent_orders = Order.objects.select_related("user").prefetch_related("items", "items__product").order_by("-ordered_at")[:4]
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
        
    staff_profiles = StaffProfile.objects.select_related("user").annotate(
                orders_handled=Count("user__orders")
                ).order_by("-orders_handled")[:4]
    
    staffPerformanceData = [
        {
            "name": sp.user.profile.full_name,
            "role": sp.role.title(),
            "orders": sp.orders_handled,
            "rating": round(sp.rating, 1),
        } for sp in staff_profiles
    ]    
    
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

    return Response({
        "salesData": salesData,
        "menuItemsData": menuItemsData,
        "hourlyOrdersData": hourlyOrdersData,
        "monthlyRevenueData": monthlyRevenueData,
        "topStatsCards": topStatsCards,
        "quickMetrics": quickMetrics,
        "recentOrdersData": recentOrdersData,
        "staffPerformanceData": staffPerformanceData,
        "inventoryAlertsData": inventoryAlertsData
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
    paginator.page_size = 100
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

        if status_update not in ["pending", "paid", "fake"]:
            return Response({"error": "Invalid payment status"}, status=status.HTTP_400_BAD_REQUEST)

        payment.status = status_update
        payment.save()

        return Response({"message": "Payment status updated successfully"}, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    except Payment.DoesNotExist:
        return Response({"error": "Payment details not found for this order"}, status=status.HTTP_404_NOT_FOUND)
    
    
#changing order status to confirmed or cancelled    
@api_view(['POST'])
@permission_classes([IsAdminUser])  # You can later replace this with custom role-based permission
def update_order_status(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        new_status = request.data.get("status")

        if new_status not in ['confirmed', 'cancelled']:
            return Response({"error": "Invalid status. Only 'confirmed' or 'cancelled' allowed."},
                            status=status.HTTP_400_BAD_REQUEST)

        if order.status in ['confirmed', 'cancelled']:
            return Response({"error": f"Order is already {order.status} and cannot be changed."},
                            status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        return Response({
            "message": f"Order successfully {new_status}.",
            "status": order.status,
            "confirmed_at": order.confirmed_at if new_status == "confirmed" else None
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