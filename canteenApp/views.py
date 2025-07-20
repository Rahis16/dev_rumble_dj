from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Cart, CartItem, Category
from .serializers import ProductSerializer, CartItemSerializer, OrderSerializer, UserProfileSerializer, CategorySerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from dj_rest_auth.views import LoginView
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LogoutView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Cart, CartItem, Order, OrderItem, UserProfile, Wallet, Payment, PaymentMethod, Table, Wallet, TransactionHistory
from decimal import Decimal
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.paginator import Paginator
from django.utils.timezone import localtime


User = get_user_model()

def home(request):
    return HttpResponse("home page")

#edit-user-profile
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_user_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return Response({'status': 'error', 'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserProfileSerializer(profile, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


#fetch-user-profile
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    profile = request.user.profile  # from OneToOne relation
    serializer = UserProfileSerializer(profile)
    return Response(serializer.data, status=status.HTTP_200_OK)


#fetch-wallet
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_wallet(request):
    try:
        # Get the wallet for the authenticated user
        wallet = Wallet.objects.get(user=request.user)
        
        # Fetch all transactions ordered by latest
        all_transactions = wallet.transactions.all().order_by('-created_at')

        # Pagination setup
        page_number = request.GET.get('page', 1)
        paginator = Paginator(all_transactions, 2)  # 30 per page

        try:
            transactions = paginator.page(page_number)
        except Exception:
            return Response({"error": "Invalid page number"}, status=status.HTTP_400_BAD_REQUEST)

        # Manually serialize paginated transactions
        transaction_data = [
            {
                "id": tx.id,
                "title": tx.title,
                "desc": tx.desc,
                "amount": str(tx.amount),
                "type": tx.type,
                "created_at": localtime(tx.created_at).strftime("%Y-%m-%d %I:%M %p")
            }
            for tx in transactions
        ]

        # Wallet info + paginated transactions
        wallet_data = {
            "id": wallet.id,
            "user_id": wallet.user.id,
            "username": wallet.user.username,
            "balance": str(wallet.balance),
            "transactions": transaction_data,
            "pagination": {
                "total": paginator.count,
                "per_page": 2,
                "current_page": transactions.number,
                "total_pages": paginator.num_pages,
                "has_next": transactions.has_next(),
                "has_previous": transactions.has_previous(),
            }
        }

        return Response(wallet_data, status=status.HTTP_200_OK)

    except Wallet.DoesNotExist:
        return Response(
            {"error": "Wallet not found for this user"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    
#fetch-categories
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

#fetch-products
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('created_at')
    serializer_class = ProductSerializer


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    

#add-to-cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))

    if not product_id:
        return Response({'status': 'error', 'message': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({'status': 'error', 'message': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get or create user's cart
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Check if product is already in cart
    existing_item = CartItem.objects.filter(cart=cart, product=product).first()

    if existing_item:
        return Response({
            'status': 'exists',
            'message': f"'{product.name}' is already in your cart.",
            'product': product.name,
            'quantity': existing_item.quantity
        }, status=status.HTTP_200_OK)

    # Create new cart item
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=quantity,
        price=product.price,
        total_price=Decimal(quantity) * product.price
    )

    return Response({
        'status': 'success',
        'message': 'Item added to cart',
        'product': product.name,
        'quantity': cart_item.quantity
    }, status=status.HTTP_201_CREATED)


#fetch-cart-items
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_cart_items(request):
    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

    cart_items = CartItem.objects.filter(cart=cart)
    serializer = CartItemSerializer(cart_items, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)



#update-cart-item
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_update(request):
    cart_item_id = request.data.get('cart_item_id')
    quantity = request.data.get('quantity')

    if cart_item_id is None or quantity is None:
        return Response({"error": "cart_item_id and quantity are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quantity = int(quantity)
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1"}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({"error": "Quantity must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    cart_item.quantity = quantity
    cart_item.save()

    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response({"status": "success", "cart_item": serializer.data}, status=status.HTTP_200_OK)



#remove-cart-item
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_remove(request):
    cart_item_id = request.data.get('cart_item_id')

    if cart_item_id is None:
        return Response({"error": "cart_item_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    cart_item.delete()

    return Response({"status": "success", "cart_item_id": cart_item_id}, status=status.HTTP_200_OK)






# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def checkout(request):
#     try:
#         cart = request.user.cart
#     except Cart.DoesNotExist:
#         return Response({"error": "No cart found for user."}, status=status.HTTP_404_NOT_FOUND)

#     cart_items = CartItem.objects.filter(cart=cart)
#     if not cart_items.exists():
#         return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

#     total_price = sum(item.quantity * item.price for item in cart_items)

#     # Create the order
#     order = Order.objects.create(
#         user=request.user,
#         total_price=total_price,
#         status='pending',
#     )

#     # Create order items
#     for item in cart_items:
#         OrderItem.objects.create(
#             order=order,
#             product=item.product,
#             quantity=item.quantity,
#             price=item.price,
#         )

#     # Clear the cart
#     cart_items.delete()

#     serializer = OrderSerializer(order, context={'request': request})
#     return Response({"status": "success", "order": serializer.data}, status=status.HTTP_201_CREATED)


#fetch-tables
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_tables(request):
    tables = Table.objects.all()
    table_data = []
    for table in tables:
        available_seats = table.capacity - table.orders.filter(status="pending").count()
        if available_seats < 0:
            available_seats = 0
        table_data.append({
            "id": table.id,
            "number": table.number,
            "capacity": table.capacity,
            "is_occupied": table.is_occupied,
            "available_seats": available_seats
        })
    return Response(table_data, status=status.HTTP_200_OK)


#checkout
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])  # To handle QR screenshot upload
def checkout(request):
    user = request.user
    payment_method = request.data.get("method")
    amount = request.data.get("amount")
    screenshot = request.FILES.get("screenshot")
    remarks = request.data.get("remarks", "")
    table_id = request.data.get("table_id")

    if not payment_method or not amount:
        return Response({"error": "Payment method and amount are required."}, status=400)
    
    if not table_id:
        return Response({"error": "Please Select a Table."}, status=400)
    
    table = None
    if table_id:
        try:
            table = Table.objects.get(id=table_id)
        except Table.DoesNotExist:
            return Response({"error": "Table not found."}, status=404)    
        
        if table.is_occupied:
            return Response({"error": "Table is already occupied."}, status=400)

    try:
        method = PaymentMethod.objects.get(name=payment_method.lower())
    except PaymentMethod.DoesNotExist:
        return Response({"error": "Invalid payment method."}, status=400)

    try:
        cart = user.cart
    except Cart.DoesNotExist:
        return Response({"error": "No cart found for user."}, status=status.HTTP_404_NOT_FOUND)

    cart_items = CartItem.objects.filter(cart=cart)
    if not cart_items.exists():
        return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

    total_price = sum(item.quantity * item.price for item in cart_items)

    if float(amount) < total_price:
        return Response({"error": "Insufficient amount for total order price."}, status=400)

    with transaction.atomic():
        # Step 1: Create Order
        order = Order.objects.create(
            user=user,
            table=table,
            total_price=total_price,
            status='pending',
        )
        
        # increase the order count for the user 
        user.profile.orders_count += 1
        user.profile.total_spent += total_price
        user.profile.save()
        
        # Create order items

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.price,
            )

        cart_items.delete()

        # Step 2: Handle payment based on method
        if method.name == "wallet":
            if not hasattr(user, 'wallet') or user.wallet.balance < Decimal(amount):
                transaction.set_rollback(True)
                return Response({"error": "Insufficient wallet balance."}, status=400)

            user.wallet.balance -= Decimal(amount)
            user.wallet.save()

            Payment.objects.create(
                user=user,
                order=order,
                method=method,
                amount=amount,
                status='paid',
                remarks=remarks,
            )
            
            purchase_items = ", ".join([f"{item.quantity}x {item.product.name}" for item in order.items.all()])    
            
            TransactionHistory.objects.create(
                    wallet=request.user.wallet,
                    title="Order Payment",
                    desc=f"Deducted {amount} for order of {purchase_items}",
                    amount=amount,
                    type="debit"
                )

        elif method.name == "qr":
            if not screenshot:
                transaction.set_rollback(True)
                return Response({"error": "Screenshot required for QR payment."}, status=400)

            Payment.objects.create(
                user=user,
                order=order,
                method=method,
                amount=amount,
                screenshot=screenshot,
                remarks=remarks,
                status="pending",  # Admin must verify
            )

        elif method.name == "counter":
            Payment.objects.create(
                user=user,
                order=order,
                method=method,
                amount=amount,
                remarks="Paid on counter - Awaiting admin confirmation.",
                status="pending"
            )

        else:
            transaction.set_rollback(True)
            return Response({"error": "Unsupported payment method."}, status=400)

        serializer = OrderSerializer(order, context={'request': request})
        return Response({"status": "success", "order": serializer.data}, status=status.HTTP_201_CREATED)



#users_orders
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_orders_view(request):
    user = request.user
    orders = Order.objects.filter(user=user).prefetch_related('items__product')

    current_orders = orders.exclude(status__in=['delivered', 'cancelled'])
    order_history = orders.filter(status='delivered')
    cancelled_order = orders.filter(status='cancelled')

    # Paginate order_history with page param 'history_page'
    history_paginator = PageNumberPagination()
    history_paginator.page_size = 2
    history_paginator.page_query_param = 'history_page'  # custom query param for order_history
    paginated_history = history_paginator.paginate_queryset(order_history, request, view=user_orders_view)
    serialized_history = OrderSerializer(paginated_history, many=True).data

    # Paginate cancelled_order with page param 'cancelled_page'
    cancelled_paginator = PageNumberPagination()
    cancelled_paginator.page_size = 2
    cancelled_paginator.page_query_param = 'cancelled_page'  # custom query param for cancelled_order
    paginated_cancelled = cancelled_paginator.paginate_queryset(cancelled_order, request, view=user_orders_view)
    serialized_cancelled = OrderSerializer(paginated_cancelled, many=True).data

    # current_orders (no pagination)
    serialized_current = OrderSerializer(current_orders, many=True).data

    return Response({
        'current_orders': serialized_current,
        'order_history': serialized_history,
        'cancelled_order': serialized_cancelled,
        'order_history_pagination': {
            'count': order_history.count(),
            'next': history_paginator.get_next_link(),
            'previous': history_paginator.get_previous_link(),
        },
        'cancelled_order_pagination': {
            'count': cancelled_order.count(),
            'next': cancelled_paginator.get_next_link(),
            'previous': cancelled_paginator.get_previous_link(),
        },
    })