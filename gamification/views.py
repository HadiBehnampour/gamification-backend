from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum
from .models import Product, Transaction, StakingPlan, Badge
from .serializers import ProductSerializer, TransactionSerializer, StakingPlanSerializer, BadgeSerializer
from users.models import User


# --- ویوهای مربوط به کاربران عادی ---

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    نمایش تاریخچه تراکنش‌های کاربر (رفع ارور Import)
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # هر کاربر فقط تراکنش‌های خودش را ببیند
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    فروشگاه برای کاربران (فقط خواندنی + متد خرید)
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category and category != 'all':
            qs = qs.filter(category=category)
        return qs

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        product = self.get_object()
        user = request.user

        # ۱. بررسی موجودی کالا
        if product.stock == 0:
            return Response({'message': 'متاسفانه موجودی این کالا تمام شده است.'}, status=400)

        # ۲. بررسی پول کاربر
        if user.current_balance < product.price:
            return Response({'message': 'موجودی AC شما برای این خرید کافی نیست.'}, status=400)

        # ۳. انجام تراکنش اتمیک (یکپارچه)
        with transaction.atomic():
            # کسر پول
            user.current_balance -= product.price
            user.save()

            # کسر موجودی کالا (اگر نامحدود نباشد)
            if product.stock > 0:
                product.stock -= 1
                product.save()

            # ثبت در تاریخچه تراکنش‌ها
            Transaction.objects.create(
                user=user,
                amount=-product.price,
                token_type='SPEND',
                description=f"خرید از فروشگاه: {product.title}"
            )

        return Response({'message': 'خرید با موفقیت انجام شد. کد پیگیری برایتان ارسال می‌شود.'})


class WalletViewSet(viewsets.ViewSet):
    """
    مدیریت کیف پول کاربر (خلاصه وضعیت + استکینگ)
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user
        # جمع‌بندی امتیازات بر اساس دسته‌بندی برای نمودار دایره‌ای/میله‌ای
        stats = {
            'performance': Transaction.objects.filter(user=user, token_type='PERFORMANCE').aggregate(Sum('amount'))[
                               'amount__sum'] or 0,
            'discipline': Transaction.objects.filter(user=user, token_type='DISCIPLINE').aggregate(Sum('amount'))[
                              'amount__sum'] or 0,
            'cultural': Transaction.objects.filter(user=user, token_type='CULTURAL').aggregate(Sum('amount'))[
                            'amount__sum'] or 0,
            'trend': Transaction.objects.filter(user=user, token_type='IDEA').aggregate(Sum('amount'))[
                         'amount__sum'] or 0,
        }
        return Response({
            'balance': user.current_balance,
            'stats': stats
        })

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        # دریافت ۲۰ تراکنش آخر کاربر (برای ویجت‌های کوچک)
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:20]
        return Response(TransactionSerializer(transactions, many=True).data)

    @action(detail=False, methods=['get'], url_path='staking-plans')
    def staking_plans(self, request):
        plans = StakingPlan.objects.filter(is_active=True)
        return Response(StakingPlanSerializer(plans, many=True).data)

    @action(detail=False, methods=['post'], url_path='join-staking')
    def join_staking(self, request):
        # منطق استیکینگ (فعلا فقط یک پیام موفقیت)
        return Response({'message': 'شما با موفقیت در این طرح سرمایه‌گذاری کردید.'})

    @action(detail=False, methods=['get'], url_path='empathy-logs')
    def empathy_logs(self, request):
        # لاگ‌های توکن همدلی (تراکنش‌های فرهنگی)
        logs = Transaction.objects.filter(token_type='CULTURAL').order_by('-created_at')[:10]
        data = [
            {'id': l.id, 'from_name': l.user.username, 'to_name': 'همکار', 'amount': l.amount, 'reason': l.description}
            for l in logs]
        return Response(data)

    @action(detail=False, methods=['post'], url_path='settlement-request')
    def settlement(self, request):
        return Response({'message': 'درخواست تسویه با موفقیت ثبت شد.'})


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticated]


# --- ویوهای مربوط به ادمین ---

class AdminProductViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل محصولات (مخصوص ادمین)
    """
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]  # در پروداکشن باید IsAdminUser باشد


class AdminWalletViewSet(viewsets.ViewSet):
    """
    پنل مدیریت بانک و تراکنش‌ها (مخصوص ادمین)
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get', 'post'], url_path='stacking-plans')
    def plans(self, request):
        if request.method == 'GET':
            return Response(StakingPlanSerializer(StakingPlan.objects.all(), many=True).data)

        serializer = StakingPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'])
    def adjustment(self, request):
        # اصلاح دستی موجودی کاربر توسط ادمین
        user_id = request.data.get('user_id')
        amount = int(request.data.get('amount'))
        reason = request.data.get('reason')
        token_type = request.data.get('type', 'PERFORMANCE').upper()

        try:
            user = User.objects.get(pk=user_id)
            user.current_balance += amount
            # اگر پاداش است، به امتیاز کل هم اضافه شود
            if amount > 0:
                user.total_points += amount
            user.save()

            Transaction.objects.create(
                user=user,
                amount=amount,
                token_type=token_type,
                description=f"اصلاح مدیریتی: {reason}"
            )
            return Response({'message': 'اصلاح موجودی انجام شد.'})
        except User.DoesNotExist:
            return Response({'error': 'کاربر یافت نشد'}, status=404)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        # مشاهده تمام تراکنش‌های سیستم برای ادمین
        transactions = Transaction.objects.all().order_by('-created_at')[:50]
        # سریالایزر دستی ساده برای جدول ادمین
        data = [{
            'id': t.id,
            'employee_name': t.user.username,
            'type_display': t.get_token_type_display(),
            'amount': t.amount,
            'description': t.description,
            'created_at': t.created_at
        } for t in transactions]
        return Response(data)