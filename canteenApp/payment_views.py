from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Payment, PaymentMethod, Order
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from rest_framework.response import Response
from django.http import HttpResponse
import csv
from django.core.paginator import Paginator

from .models import Payment
from .payment_serializers import PaymentSerializerAdmin

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





class PaymentListAPIView(generics.ListAPIView):
    serializer_class = PaymentSerializerAdmin
    queryset = Payment.objects.select_related("user", "order", "method").all().order_by("-created_at")
    

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get("status")
        method_param = self.request.query_params.get("method")
        search = self.request.query_params.get("search")

        if status_param and status_param != "all":
            queryset = queryset.filter(status=status_param)

        if method_param and method_param != "all":
            queryset = queryset.filter(method__name__iexact=method_param)

        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(order__id__icontains=search)
                | Q(id__icontains=search)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # ✅ Export CSV
        if request.query_params.get("export") == "csv":
            return self.export_csv(queryset)

        # ✅ Pagination
        page = request.query_params.get("page", 1)
        limit = request.query_params.get("limit", 10)

        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            return Response({"error": "Invalid pagination parameters"}, status=status.HTTP_400_BAD_REQUEST)

        paginator = Paginator(queryset, limit)

        try:
            payments_page = paginator.page(page)
        except PageNotAnInteger:
            payments_page = paginator.page(1)
        except EmptyPage:
            return Response({"error": "Page out of range"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(payments_page.object_list, many=True)

        return Response({
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "results": serializer.data,
        })

    def export_csv(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payments.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "ID", "User", "Order ID", "Amount", "Method", "Status", "Transaction ID", "Created At"
        ])

        for p in queryset:
            writer.writerow([
                p.id,
                p.user.get_full_name(),
                p.order.id,
                f"{p.amount:.2f}",
                p.method.name if p.method else "",
                p.status,
                f"TXN{p.id:06d}",
                p.created_at.strftime("%Y-%m-%d %H:%M"),
            ])

        return response