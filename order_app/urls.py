from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path

router = DefaultRouter()
router.register(r"pizzas", PizzaViewSet, basename="pizza")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns =[


 path("deliveries/", MyDeliveriesView.as_view(), name="my-deliveries"),
    path("delivery-boy/", MyAssignedDeliveriesView.as_view(), name="delivery-boy"),
    path("update-delivery/<int:delivery_id>/", UpdateDeliveryStatusView.as_view(), name="update-delivery"),
]