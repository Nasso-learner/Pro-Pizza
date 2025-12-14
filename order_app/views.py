from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Order, Pizza
from .serializers import OrderSerializer, PizzaSerializer
from .kafka_producer import send_order_event

class PizzaViewSet(viewsets.ModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Send Kafka event
        send_order_event("ORDER_CREATED", serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Send Kafka event
        send_order_event("ORDER_UPDATED", serializer.data)

        return Response(serializer.data, status=status.HTTP_200_OK)
    


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Order, Delivery, DeliveryBoy


class MyDeliveriesView(APIView):
    """
    Customers view their orders and delivery details
    """
    def get(self, request):
        userinfo = request.session.get("userinfo")
        if not userinfo:
            return Response({"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        keycloak_id = userinfo.get("sub")
        username = userinfo.get("preferred_username")

        orders = Order.objects.all()
        data = []
        delivery_boy = DeliveryBoy.objects.get(keycloak_id = keycloak_id)
        for order in orders:

            delivery = Delivery.objects.filter(order=order,delivery_boy=delivery_boy).first()
            if delivery :
                data.append({
                    "order_id": order.id,
                    "pizza": order.pizza.name,
                    "status": order.status,
                    "delivery_status": delivery.status if delivery else "Not assigned",
                    "delivery_location": delivery.delivery_location if delivery else None,
                    "delivery_boy": delivery.delivery_boy.name if delivery else None,
                })

        return Response({
            "username": username,
            "deliveries": data
        })


class MyAssignedDeliveriesView(APIView):
    """
    Delivery boys view their assigned deliveries
    """
    def get(self, request):
        userinfo = request.session.get("userinfo")
        if not userinfo:
            return Response({"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        keycloak_id = userinfo.get("sub")
        delivery_boy = DeliveryBoy.objects.filter(keycloak_id=keycloak_id).first()
        if not delivery_boy:
            return Response({"error": "Not registered as a delivery boy"}, status=status.HTTP_403_FORBIDDEN)

        deliveries = Delivery.objects.filter(delivery_boy=delivery_boy)
        data = [
            {
                "delivery_id": d.id,
                "order_id": d.order.id,
                "customer": d.order.customer_name,
                "pizza": d.order.pizza.name,
                "delivery_location": d.delivery_location,
                "status": d.status,
            }
            for d in deliveries
        ]

        return Response({
            "delivery_boy": delivery_boy.name,
            "assigned_deliveries": data
        })

class UpdateDeliveryStatusView(APIView):
    """
    Delivery boys update delivery status (e.g. OUT_FOR_DELIVERY, DELIVERED)
    """
    def post(self, request, delivery_id):
        userinfo = request.session.get("userinfo")
        if not userinfo:
            return Response({"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        keycloak_id = userinfo.get("sub")
        try:
            delivery = Delivery.objects.get(id=delivery_id, delivery_boy__keycloak_id=keycloak_id)
        except Delivery.DoesNotExist:
            return Response({"error": "Delivery not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

        status_update = request.data.get("status")
        if status_update not in dict(Delivery.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        delivery.status = status_update
        if status_update == "DELIVERED":
            delivery.delivered_at = timezone.now()
        delivery.save()

        return Response({
            "message": "Delivery status updated successfully",
            "new_status": delivery.status
        })
