from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import ShopItem, Purchase
from .serializers import ShopItemSerializer, PurchaseSerializer
from gamification.models import Transaction


class ShopItemViewSet(viewsets.ModelViewSet):
    queryset = ShopItem.objects.filter(is_active=True)
    serializer_class = ShopItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='buy')
    def buy_item(self, request, pk=None):
        item = self.get_object()
        user = request.user

        if item.price > user.current_balance:
            return Response({'error': 'Insufficient balance'}, status=400)

        if item.stock == 0:
            return Response({'error': 'Out of stock'}, status=400)

        with transaction.atomic():
            item_name = item.name

            # FIX: استفاده از format بجای f-string
            desc_text = "خرید آیتم: {}".format(item_name)

            Transaction.objects.create(
                user=user,
                amount=-item.price,
                token_type='PURCHASE',
                description=desc_text
            )

            Purchase.objects.create(
                user=user,
                item=item,
                status='PENDING'
            )

            if item.stock > 0:
                item.stock -= 1
                item.save()

        return Response({'message': 'Purchase successful'})