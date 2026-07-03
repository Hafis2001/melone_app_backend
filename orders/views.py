import bcrypt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from .models import Owner, Staff, Order
from decimal import Decimal

# Helper functions for bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class OwnerRegisterView(APIView):
    def post(self, request):
        name = request.data.get('name')
        shop_name = request.data.get('shop_name')
        email = request.data.get('email')
        password = request.data.get('password')

        if Owner.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        owner = Owner.objects.create(
            name=name,
            shop_name=shop_name,
            email=email,
            password=hash_password(password)
        )
        return Response({
            "success": True,
            "owner_id": owner.id,
            "name": owner.name,
            "shop_name": owner.shop_name,
            "shop_code": owner.shop_code
        })

class OwnerLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            owner = Owner.objects.get(email=email)
            if check_password(password, owner.password):
                return Response({
                    "success": True,
                    "owner_id": owner.id,
                    "name": owner.name,
                    "shop_name": owner.shop_name,
                    "shop_code": owner.shop_code
                })
        except Owner.DoesNotExist:
            pass
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class StaffCreateView(APIView):
    def post(self, request):
        owner_id = request.data.get('owner_id')
        name = request.data.get('name')
        username = request.data.get('username')
        password = request.data.get('password')

        if Staff.objects.filter(owner_id=owner_id, username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        owner = get_object_or_404(Owner, id=owner_id)
        staff = Staff.objects.create(
            owner=owner,
            name=name,
            username=username,
            password=hash_password(password)
        )
        return Response({
            "success": True,
            "staff_id": staff.id,
            "username": staff.username
        })

class StaffListView(APIView):
    def get(self, request):
        owner_id = request.query_params.get('owner_id')
        staff_members = Staff.objects.filter(owner_id=owner_id)
        data = [
            {
                "id": s.id,
                "name": s.name,
                "username": s.username,
                "is_active": s.is_active,
                "device_id": s.device_id,
                "created_at": s.created_at
            } for s in staff_members
        ]
        return Response(data)

class StaffToggleView(APIView):
    def patch(self, request, staff_id):
        staff = get_object_or_404(Staff, id=staff_id)
        staff.is_active = not staff.is_active
        staff.save()
        return Response({"success": True, "is_active": staff.is_active})

class StaffLoginView(APIView):
    def post(self, request):
        shop_code = request.data.get('shop_code')
        username = request.data.get('username')
        password = request.data.get('password')
        device_id = request.data.get('device_id')

        if not shop_code or not username or not password:
             return Response({"error": "shop_code, username, and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            owner = Owner.objects.get(shop_code=shop_code)
            staff = Staff.objects.get(username=username, owner=owner)
            
            if check_password(password, staff.password):
                if not staff.is_active:
                    return Response({"error": "Account disabled"}, status=status.HTTP_401_UNAUTHORIZED)
                
                if device_id and not staff.device_id:
                    staff.device_id = device_id
                    staff.save()
                
                return Response({
                    "success": True,
                    "staff_id": staff.id,
                    "name": staff.name,
                    "owner_name": staff.owner.name,
                    "shop_name": staff.owner.shop_name,
                    "shop_code": staff.owner.shop_code
                })
        except Owner.DoesNotExist:
            pass
        except Staff.DoesNotExist:
            pass
            
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class SyncOrdersView(APIView):
    def post(self, request):
        staff_id = request.data.get('staff_id')
        orders_data = request.data.get('orders', [])

        try:
            staff = Staff.objects.get(id=staff_id)
        except Staff.DoesNotExist:
            return Response({"error": "Invalid staff_id"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not staff.is_active:
            return Response({"error": "Staff account is disabled"}, status=status.HTTP_401_UNAUTHORIZED)

        received = len(orders_data)
        upserted = 0

        for order_data in orders_data:
            order_id = order_data.get('order_id') or order_data.get('id')
            if not order_id:
                continue

            total = order_data.get('total', 0)
            items = order_data.get('items', [])
            created_at_str = order_data.get('created_at')

            try:
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                else:
                    created_at = timezone.now()
            except ValueError:
                created_at = timezone.now()

            defaults = {
                'total': Decimal(str(total)),
                'items': items,
                'created_at': created_at,
                'raw_data': order_data
            }

            Order.objects.update_or_create(
                order_id=order_id,
                staff=staff,
                defaults=defaults
            )
            upserted += 1

        return Response({
            "success": True,
            "received": received,
            "upserted": upserted
        })

class OwnerOrdersView(APIView):
    def get(self, request):
        owner_id = request.query_params.get('owner_id')
        if not owner_id:
            return Response({"error": "owner_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        queryset = Order.objects.filter(staff__owner_id=owner_id).order_by('-created_at')

        # Filter by date ?date=YYYY-MM-DD
        date_param = request.query_params.get('date')
        if date_param:
            try:
                filter_date = datetime.strptime(date_param, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date=filter_date)
            except ValueError:
                pass

        # Filter by ?filter=today or week
        filter_param = request.query_params.get('filter')
        if filter_param == 'today':
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(created_at__gte=today)
        elif filter_param == 'week':
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today - timedelta(days=today.weekday())
            queryset = queryset.filter(created_at__gte=week_start)

        data = [
            {
                "order_id": o.order_id,
                "total": float(o.total),
                "items": o.items,
                "created_at": o.created_at,
                "synced_at": o.synced_at,
                "staff_name": o.staff.name if o.staff else "Unknown"
            } for o in queryset
        ]
        return Response(data)

class OwnerRevenueView(APIView):
    def get(self, request):
        owner_id = request.query_params.get('owner_id')
        if not owner_id:
            return Response({"error": "owner_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        base_qs = Order.objects.filter(staff__owner_id=owner_id)

        # Total
        total_aggregate = base_qs.aggregate(total_revenue=Sum('total'), total_orders=Count('id'))
        total_revenue = total_aggregate.get('total_revenue') or Decimal('0.00')
        total_orders = total_aggregate.get('total_orders') or 0

        # Today
        today_aggregate = base_qs.filter(created_at__gte=today_start).aggregate(today_revenue=Sum('total'), today_orders=Count('id'))
        today_revenue = today_aggregate.get('today_revenue') or Decimal('0.00')
        today_orders = today_aggregate.get('today_orders') or 0

        # Week
        week_aggregate = base_qs.filter(created_at__gte=week_start).aggregate(week_revenue=Sum('total'), week_orders=Count('id'))
        week_revenue = week_aggregate.get('week_revenue') or Decimal('0.00')
        week_orders = week_aggregate.get('week_orders') or 0

        return Response({
            "total_revenue": float(total_revenue),
            "today_revenue": float(today_revenue),
            "total_orders": total_orders,
            "today_orders": today_orders,
            "week_revenue": float(week_revenue),
            "week_orders": week_orders
        })
