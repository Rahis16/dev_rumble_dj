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
from .models import Order, Payment
from .serializers import OrderSerializer2


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

    if status_filter:
        orders = orders.filter(status=status_filter)
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
    paginator.page_size = 30
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
