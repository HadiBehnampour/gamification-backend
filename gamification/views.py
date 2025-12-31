from rest_framework import viewsets, permissions
from .models import Transaction, Badge
from .serializers import TransactionSerializer, BadgeSerializer

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # هر کس فقط تراکنش‌های خودش را ببیند
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')

class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticated]