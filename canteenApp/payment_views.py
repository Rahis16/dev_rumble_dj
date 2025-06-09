from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Payment, PaymentMethod, Wallet, Order
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_with_wallet(request):
    user = request.user
    order_id = request.data.get("order")
    amount = request.data.get("amount")

    order = get_object_or_404(Order, id=order_id)
    method = get_object_or_404(PaymentMethod, name="wallet")

    if not hasattr(user, 'wallet') or user.wallet.balance < float(amount):
        return Response({"error": "Insufficient wallet balance"}, status=400)

    # Deduct and create payment
    user.wallet.balance -= float(amount)
    user.wallet.save()

    payment = Payment.objects.create(
        user=user,
        order=order,
        method=method,
        amount=amount,
        status='paid'
    )

    return Response({"message": "Payment successful via wallet", "payment_id": payment.id}, status=201)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])  # For handling file uploads
def pay_with_qr(request):
    user = request.user
    order_id = request.data.get("order")
    amount = request.data.get("amount")
    remarks = request.data.get("remarks", "")
    screenshot = request.FILES.get("screenshot")

    if not order_id or not amount or not screenshot:
        return Response({"error": "Order, amount, and screenshot are required."}, status=400)

    order = get_object_or_404(Order, id=order_id)
    method = get_object_or_404(PaymentMethod, name="qr")

    payment = Payment.objects.create(
        user=user,
        order=order,
        method=method,
        amount=amount,
        remarks=remarks,
        screenshot=screenshot,
        status="pending",  # pending until admin verifies
    )

    return Response({"message": "QR payment submitted. Awaiting admin approval.", "payment_id": payment.id}, status=201)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_on_counter(request):
    user = request.user
    order_id = request.data.get("order")
    amount = request.data.get("amount")

    if not order_id or not amount:
        return Response({"error": "Order and amount are required."}, status=400)

    order = get_object_or_404(Order, id=order_id)
    method = get_object_or_404(PaymentMethod, name="counter")

    payment = Payment.objects.create(
        user=user,
        order=order,
        method=method,
        amount=amount,
        status="pending",  # Admin will approve
        remarks="Paid on counter - Awaiting admin confirmation."
    )

    return Response({"message": "Counter payment recorded. Inform admin with your username.", "payment_id": payment.id}, status=201)
