# Django views and serializers for table management only for clean management

from rest_framework import generics, status, views
from rest_framework.response import Response
from django.utils import timezone
from .models import Table, Reservation, TableUpdateLog
from .table_admin_serializers import TableSerializer, ReservationSerializer, TableUpdateLogSerializer, ReservationCreateSerializer


class TableListAPIView(generics.ListAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer


class TableStatusUpdateAPIView(views.APIView):
    def patch(self, request, pk):
        try:
            table = Table.objects.get(pk=pk)
            status = request.data.get("status")
            if status in dict(Table.STATUS_CHOICES):
                table.status = status
                table.save()
                return Response({"message": "Status updated"})
            else:
                return Response({"error": "Invalid status"}, status=400)
        except Table.DoesNotExist:
            return Response({"error": "Table not found"}, status=404)


class ReservationListAPIView(generics.ListAPIView):
    serializer_class = ReservationSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        time = self.request.query_params.get("time")
        # search = self.request.query_params.get("search")
        # area = self.request.query_params.get("area")


        queryset = Reservation.objects.all()
        if date:
            queryset = queryset.filter(date=date)
        if time:
            queryset = queryset.filter(time=time)
        # if search:
        #     queryset = queryset.filter(customer_name__icontains=search)
        # if area:
        #     queryset = queryset.filter(table__area=area)
            
            
        return queryset


class ReservationCreateAPIView(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationCreateSerializer


class ReservationUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationCreateSerializer
    lookup_field = 'id'


class TableUpdateLogListAPIView(generics.ListAPIView):
    queryset = TableUpdateLog.objects.order_by('-created_at')[:20]
    serializer_class = TableUpdateLogSerializer