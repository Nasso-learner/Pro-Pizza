from rest_framework import serializers
from .models import Order, Pizza

class PizzaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pizza
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    pizza = PizzaSerializer(read_only=True)
    pizza_id = serializers.PrimaryKeyRelatedField(
        queryset=Pizza.objects.all(), source="pizza", write_only=True
    )

    class Meta:
        model = Order
        fields = ["id", "customer_name", "pizza", "pizza_id", "quantity", "status", "created_at"]
