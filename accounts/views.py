from django.shortcuts import render, redirect, get_object_or_404

from django.core.mail import send_mail
from django.core.paginator import Paginator

from django.conf import settings
import logging

from .models import MaintenanceTask, MaintenanceReport, MaintenanceReportPhoto

from .forms import MaintenanceTaskForm, MaintenanceReportForm

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods

import json
import mimetypes

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib import messages

from django.contrib.auth.models import User

from django.db.models import Count, Sum, Q, F, OuterRef, Subquery
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from django.utils import timezone
from django.utils.dateparse import parse_date

from django.views.decorators.http import require_POST

from django.http import FileResponse, Http404, JsonResponse
from urllib.parse import urlsplit

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import asin, cos, radians, sin, sqrt
from PIL import Image, UnidentifiedImageError
from django.core.files.base import ContentFile
from io import BytesIO
from uuid import uuid4


SERVICE_AREA_BOUNDARY = (
    (14.392, 120.945),
    (14.392, 120.980),
    (14.425, 121.020),
    (14.475, 121.035),
    (14.525, 121.025),
    (14.525, 120.970),
    (14.490, 120.950),
    (14.445, 120.935),
    (14.410, 120.940),
)


def is_within_service_area(latitude, longitude):
    inside = False
    j = len(SERVICE_AREA_BOUNDARY) - 1
    for i, (lat_i, lng_i) in enumerate(SERVICE_AREA_BOUNDARY):
        lat_j, lng_j = SERVICE_AREA_BOUNDARY[j]
        if ((lng_i > longitude) != (lng_j > longitude)
                and latitude < (lat_j - lat_i) * (longitude - lng_i)
                / (lng_j - lng_i) + lat_i):
            inside = not inside
        j = i
    return inside

from django.urls import reverse

import json

from .models import UserProfile, Consumer, Order, OrderItem, ReturnRequest, ReturnRequestItem, ReturnRequestImage, Conversation, Message, ContactMessage, Sale, Product, ProductImage, SaleItem, Category, InventoryTransaction, EmailVerification, Notification, StationAvailability, WifiConfiguration, AdminAnnouncementImage


from .forms import (

    CustomUserCreationForm, 

    StaffUserCreationForm, 

    OrderForm, 

    MessageForm, 

    ProductForm, 

    SaleForm, 

    CategoryForm,

    EmailRegistrationForm,

    GoogleProfileCompletionForm,

)



























from .decorators import admin_required, staff_required, rider_required, customer_required, role_required


logger = logging.getLogger(__name__)


def _next_order_number(exclude_order_id=None):
    orders = Order.objects.all()
    if exclude_order_id is not None:
        orders = orders.exclude(pk=exclude_order_id)
    used_numbers = set(orders.values_list('order_number', flat=True))
    used_numbers.update(
        Sale.objects.exclude(order_number__isnull=True).values_list(
            'order_number', flat=True
        )
    )

    number = 1000
    while f'ORD-{number}' in used_numbers:
        number += 1
    return f'ORD-{number}'































# Station coordinates for BLK 19 LOT 1 PHASE 1 ST.LOUIE VILLAGE ADMIRAL TALON 3 LAS PIÑAS CITY















STATION_LAT = 14.4471549















STATION_LNG = 121.0030659















STATION_ADDRESS = "BLK 19 LOT 1 PHASE 1 ST.LOUIE VILLAGE ADMIRAL TALON 3, Las Piñas City, 1747"

DELIVERY_BASE_FEE = Decimal('20.00')
FREE_DELIVERY_AREA_KEYWORDS = ('hongkong', 'hong kong')
DEFAULT_DELIVERY_FEE_RATES = {
    'up_to_2km': DELIVERY_BASE_FEE,
    'up_to_3km': Decimal('30.00'),
}


def calculate_delivery_fee(latitude, longitude, address='', fee_rates=None):
    """Return the tiered fee, distance, area, and approval state for an order."""
    normalized_address = (address or '').lower().replace('-', ' ')
    rates = fee_rates or DEFAULT_DELIVERY_FEE_RATES
    if latitude is None or longitude is None:
        if any(keyword in normalized_address for keyword in FREE_DELIVERY_AREA_KEYWORDS):
            return Decimal('0.00'), Decimal('0.00'), 'Hongkong / Station Area', False
        return rates['up_to_2km'], Decimal('0.00'), 'Registered Address', False

    earth_radius_km = 6371
    lat_delta = radians(float(latitude) - STATION_LAT)
    lng_delta = radians(float(longitude) - STATION_LNG)
    station_lat = radians(STATION_LAT)
    customer_lat = radians(float(latitude))
    distance = 2 * earth_radius_km * asin(sqrt(
        sin(lat_delta / 2) ** 2
        + cos(station_lat) * cos(customer_lat) * sin(lng_delta / 2) ** 2
    ))
    distance_km = Decimal(str(distance)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    area = 'Talon 3' if 'talon 3' in normalized_address or 'st. louie' in normalized_address else 'Outside Village'
    if any(keyword in normalized_address for keyword in FREE_DELIVERY_AREA_KEYWORDS):
        return Decimal('0.00'), distance_km, 'Hongkong / Station Area', False
    if Decimal(str(distance)) <= Decimal('0.20'):
        return Decimal('0.00'), distance_km, area, False
    if distance_km <= Decimal('2.00'):
        fee = rates['up_to_2km']
    else:
        fee = rates['up_to_3km']
    return fee, distance_km, area, distance_km > Decimal('5.00')


def calculate_buy_ten_get_one_discount(product_quantities):
    """Discount the cheapest unit for every 11 items in a customer order."""
    free_item_count = sum(quantity for _, quantity in product_quantities) // 11
    discount = Decimal('0.00')
    for product, quantity in sorted(product_quantities, key=lambda entry: entry[0].price):
        free_from_product = min(free_item_count, quantity)
        discount += product.price * free_from_product
        free_item_count -= free_from_product
        if free_item_count == 0:
            break
    return discount































# ===================== LOGIN / LOGOUT / REGISTER =====================















def login_view(request):

    if request.user.is_authenticated:

        return redirect('dashboard_redirect')



    if request.method == 'POST':















        username = request.POST.get('username')















        password = request.POST.get('password')















        user = authenticate(request, username=username, password=password)















        















        if user is not None:















            login(request, user)















            role = user.profile.role















            if role == 'admin':















                return redirect('admin_dashboard')















            elif role == 'staff':















                return redirect('staff_dashboard')















            elif role == 'rider':















                return redirect('rider_dashboard')















            else:















                return redirect('customer_dashboard')















        else:















            messages.error(request, 'Invalid username or password.')















    















    return render(request, 'accounts/login.html')































def logout_view(request):















    logout(request)















    return redirect('login')































def register_view(request):

    if request.method == 'POST':

        form = CustomUserCreationForm(request.POST)

        if form.is_valid():

            # Extract form data

            username = form.cleaned_data['username']

            email = form.cleaned_data['email']

            first_name = form.cleaned_data['first_name']

            last_name = form.cleaned_data['last_name']

            password1 = form.cleaned_data['password1']

            phone_number = form.cleaned_data['phone_number']

            address = form.cleaned_data['address']

            

            # Check if username or email already exists

            if User.objects.filter(username=username).exists():

                messages.error(request, 'Username already exists.')

                return render(request, 'accounts/register.html', {'form': form})

            if User.objects.filter(email=email).exists():

                messages.error(request, 'Email already registered.')

                return render(request, 'accounts/register.html', {'form': form})

            

            try:

                user = User.objects.create_user(

                    username=username,

                    email=email,

                    password=password1,

                    first_name=first_name,

                    last_name=last_name

                )



                user.profile.phone_number = phone_number

                user.profile.address = address

                user.profile.role = 'customer'

                user.profile.save()



                Consumer.objects.create(user=user)



                messages.success(request, 'Registration successful! Please login.')

                return redirect('login')



            except Exception as e:

                messages.error(request, f'Error creating account: {str(e)}')

                return render(request, 'accounts/register.html', {'form': form})

    else:

        form = CustomUserCreationForm()

    

    return render(request, 'accounts/register.html', {'form': form})





# OTP verification flow removed. Registration now creates users immediately.





def dashboard_redirect(request):

    if not request.user.is_authenticated:

        return redirect('login')



    try:







        role = request.user.profile.role







    except (UserProfile.DoesNotExist, AttributeError):







        messages.error(request, 'Unable to determine your account role. Please contact support.')







        return redirect('login')















    if role == 'admin':







        return redirect('admin_dashboard')







    elif role == 'staff':







        return redirect('staff_dashboard')







    elif role == 'rider':







        return redirect('rider_dashboard')







    else:







        return redirect('customer_dashboard')































# ===================== DASHBOARDS =====================















@admin_required















def admin_dashboard(request):















    total_users = User.objects.count()















    total_customers = User.objects.filter(profile__role='customer').count()















    total_staff = User.objects.filter(profile__role='staff').count()















    total_riders = User.objects.filter(profile__role='rider').count()















    active_riders_count = User.objects.filter(profile__role='rider', is_active=True).count()















    total_orders = Order.objects.count()















    pending_orders = Order.objects.filter(status='pending').count()















    recent_orders = Order.objects.all().order_by('-created_at')[:10]















    















    today = timezone.localdate()















    today_sales = Sale.objects.filter(
        created_at__date=today,
        status='completed',
        items__isnull=False,
    ).distinct()















    today_revenue = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    today_transactions = today_sales.count()















    today_items_sold = SaleItem.objects.filter(















        sale__in=today_sales















    ).aggregate(Sum('quantity'))['quantity__sum'] or 0















    















    total_products = Product.objects.filter(is_active=True).count()















    















    low_stock_products = Product.objects.filter(















        is_active=True,















        stock_quantity__lte=F('reorder_level')















    )[:10]















    low_stock_count = low_stock_products.count()















    















    recent_pos_sales = today_sales.select_related(
        'customer', 'cashier', 'rider'
    ).prefetch_related('items').order_by('-created_at')[:10]















    















    month_start = timezone.now().replace(day=1).date()















    top_products_month = SaleItem.objects.filter(















        sale__created_at__date__gte=month_start,















        sale__status='completed'















    ).values('product__name').annotate(















        total_quantity=Sum('quantity'),















        total_revenue=Sum('subtotal')















    ).order_by('-total_quantity')[:5]















    















    start_date = today
    end_date = today















    















    date_from = start_date.strftime('%Y-%m-%d')















    date_to = end_date.strftime('%Y-%m-%d')















    















    sales = Sale.objects.filter(















        created_at__date__gte=start_date,















        created_at__date__lte=end_date,















        status='completed'















    ).select_related('customer', 'cashier').prefetch_related('items')















    















    total_sales = sales.count()















    total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    average_sale = total_revenue / total_sales if total_sales > 0 else 0















    















    total_items_sold = SaleItem.objects.filter(















        sale__in=sales















    ).aggregate(Sum('quantity'))['quantity__sum'] or 0















    















    cash_total = 0















    gcash_total = 0















    cash_count = 0















    gcash_count = 0















    















    for sale in sales:















        if sale.payment_method == 'cash':















            cash_total += sale.total_amount















            cash_count += 1















        elif sale.payment_method == 'gcash':















            gcash_total += sale.total_amount















            gcash_count += 1















    















    daily_sales_data = []















    current_date = start_date















    















    sales_by_date = {}















    for sale in sales:















        sale_date = sale.created_at.date()















        if sale_date not in sales_by_date:















            sales_by_date[sale_date] = {'cash': 0, 'gcash': 0}















        if sale.payment_method == 'cash':















            sales_by_date[sale_date]['cash'] += sale.total_amount















        elif sale.payment_method == 'gcash':















            sales_by_date[sale_date]['gcash'] += sale.total_amount















    















    while current_date <= end_date:















        day_data = sales_by_date.get(current_date, {'cash': 0, 'gcash': 0})















        day_label = current_date.strftime('%a %d')















        















        daily_sales_data.append({















            'day_label': day_label,















            'day_number': current_date.day,















            'day_name': current_date.strftime('%A'),















            'full_date': current_date.strftime('%Y-%m-%d'),















            'month_year': current_date.strftime('%B %Y'),















            'cash_total': float(day_data['cash']),















            'gcash_total': float(day_data['gcash']),















            'total': float(day_data['cash'] + day_data['gcash'])















        })















        















        current_date += timedelta(days=1)















    















    top_product_image = ProductImage.objects.filter(
        product_id=OuterRef('product_id'),
    ).order_by('-is_main', 'created_at', 'pk').values('image')[:1]

    top_products_refill = SaleItem.objects.filter(
        sale__in=sales,
        product__product_type='refill',
    ).values(
        'product_id',
        'product__name',
        'product__container_type',
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal'),
        image_path=Subquery(top_product_image),
    ).order_by('-total_quantity')[:10]

    top_products_gallon = SaleItem.objects.filter(
        sale__in=sales,
        product__product_type='gallon',
    ).values(
        'product_id',
        'product__name',
        'product__container_type',
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal'),
        image_path=Subquery(top_product_image),
    ).order_by('-total_quantity')[:10]















    















    maintenance_tasks = MaintenanceTask.objects.exclude(
        status='Completed'
    ).order_by('scheduled_date', 'scheduled_time')[:10]
    maintenance_reports = MaintenanceReport.objects.exclude(
        status='Resolved'
    ).order_by('-created_at')[:10]

    context = {

        'announcement_categories': AdminAnnouncementImage.CATEGORY_CHOICES,

        'station_is_open': StationAvailability.objects.values_list(
            'is_open', flat=True
        ).first() is not False,
        'maintenance_tasks': maintenance_tasks,
        'maintenance_reports': maintenance_reports,


        'total_users': total_users,















        'total_customers': total_customers,















        'total_staff': total_staff,















        'total_riders': total_riders,















        'active_riders_count': active_riders_count,















        'total_orders': total_orders,















        'pending_orders': pending_orders,















        'recent_orders': recent_orders,















        'today_revenue': today_revenue,















        'today_transactions': today_transactions,















        'today_items_sold': today_items_sold,















        'total_products': total_products,















        'low_stock_products': low_stock_products,















        'low_stock_count': low_stock_count,















        'recent_pos_sales': recent_pos_sales,















        'top_products_month': top_products_month,















        'date_from': date_from,















        'date_to': date_to,















        'total_sales': total_sales,















        'total_revenue': total_revenue,
        'average_sale': average_sale,















        'total_items_sold': total_items_sold,















        'cash_total': cash_total,















        'gcash_total': gcash_total,















        'cash_count': cash_count,















        'gcash_count': gcash_count,















        'daily_sales_data': daily_sales_data,















        'top_products_refill': top_products_refill,
        'top_products_gallon': top_products_gallon,















        'recent_sales': sales[:20],















        'date_range': {















            'start_date': start_date,















            'end_date': end_date















        }















    }















    return render(request, 'accounts/admin_dashboard.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def admin_announcement_api(request):
    if request.method == 'GET':
        announcements = AdminAnnouncementImage.objects.all()
        return JsonResponse({
            'announcements': [
                {
                    'id': announcement.id,
                    'url': request.build_absolute_uri(announcement.image.url) if announcement.image else '',
                    'category': announcement.category,
                    'category_label': announcement.get_category_display(),
                    'headline': announcement.headline,
                    'description': announcement.description,
                }
                for announcement in announcements
            ]
        })

    uploaded_image = request.FILES.get('image')
    if uploaded_image and (
        not uploaded_image.content_type
        or not uploaded_image.content_type.startswith('image/')
    ):
        return JsonResponse({'error': 'Please upload a valid image.'}, status=400)

    headline = request.POST.get('headline', '').strip()
    description = request.POST.get('description', '').strip()
    category = request.POST.get('category', 'important')
    valid_categories = {value for value, _label in AdminAnnouncementImage.CATEGORY_CHOICES}
    if len(headline) > 120 or len(description) > 280:
        return JsonResponse({'error': 'Some announcement fields exceed their character limit.'}, status=400)
    if category not in valid_categories:
        return JsonResponse({'error': 'Please choose a valid announcement type.'}, status=400)

    with transaction.atomic():
        announcement = AdminAnnouncementImage.objects.create(
            image=uploaded_image,
            category=category,
            headline=headline,
            description=description,
        )
        announcement_url = reverse('customer_dashboard') + f'#customer-announcement-{announcement.id}'
        announcement_title = headline or announcement.get_category_display()
        announcement_description = description or 'A new station announcement is available.'
        customer_users = User.objects.filter(profile__role='customer')
        Notification.objects.bulk_create([
            Notification(
                recipient=customer,
                title=announcement_title,
                description=announcement_description,
                category='announcement',
                severity='info',
                target_url=announcement_url,
            )
            for customer in customer_users
        ])
    return JsonResponse({
        'id': announcement.id,
        'url': request.build_absolute_uri(announcement.image.url) if announcement.image else '',
        'category': announcement.category,
        'category_label': announcement.get_category_display(),
        'headline': announcement.headline,
        'description': announcement.description,
    }, status=201)


@admin_required
@require_http_methods(["DELETE"])
def admin_announcement_detail_api(request, announcement_id):
    announcement = get_object_or_404(AdminAnnouncementImage, id=announcement_id)
    announcement_url = reverse('customer_dashboard') + f'#customer-announcement-{announcement.id}'
    Notification.objects.filter(
        category='announcement',
        target_url=announcement_url,
    ).delete()
    if announcement.image:
        announcement.image.delete(save=False)
    announcement.delete()
    return JsonResponse({'success': True})









def maintenance(request):

    """

    Maintenance management page for admins

    """

    context = {}

    return render(request, 'accounts/maintenance.html', context)















































@staff_required















def staff_dashboard(request):















    today = timezone.localdate()































    today_sales = Sale.objects.filter(





        created_at__date=today,





        status='completed',
        items__isnull=False,





    ).distinct()















    today_transactions = today_sales.count()















    today_revenue = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    today_items_sold = SaleItem.objects.filter(















        sale__in=today_sales















    ).aggregate(Sum('quantity'))['quantity__sum'] or 0































    products = Product.objects.filter(is_active=True).select_related('category').order_by('name')
    refill_products = products.filter(product_type='refill')
    gallon_products = products.filter(product_type='gallon')
    categories = Category.objects.all().order_by('name')















    customers = User.objects.filter(profile__role='customer', is_active=True).order_by('first_name')















    riders = User.objects.filter(profile__role='rider', is_active=True).order_by('first_name')















    active_riders_count = riders.count()































    low_stock_products = Product.objects.filter(















        is_active=True,















        stock_quantity__lte=F('reorder_level')















    )









    low_stock_count = low_stock_products.count()



    # Fetch maintenance tasks and reports for staff dashboard

    maintenance_tasks = MaintenanceTask.objects.exclude(status='Completed').order_by('scheduled_date', 'scheduled_time')[:10]

    

    maintenance_reports = MaintenanceReport.objects.exclude(status='Resolved').order_by('-created_at')[:10]



    recent_pos_sales = Sale.objects.filter(









        created_at__date=today















    ).select_related('customer', 'cashier', 'rider').prefetch_related('items').order_by('-created_at')[:20]































    context = {















        'today_transactions': today_transactions,















        'today_revenue': today_revenue,















        'today_items_sold': today_items_sold,















        'active_riders_count': active_riders_count,















        'products': products,
        'refill_products': refill_products,
        'gallon_products': gallon_products,
        'categories': categories,















        'customers': customers,















        'riders': riders,















        'recent_pos_sales': recent_pos_sales,















        'low_stock_products': low_stock_products,















        'low_stock_count': low_stock_count,















        'maintenance_tasks': maintenance_tasks,

        'maintenance_reports': maintenance_reports,

    }



    return render(request, 'accounts/staff_dashboard.html', context)













































# ===================== RIDER DASHBOARD =====================















@rider_required















def rider_dashboard(request):















    my_orders = Order.objects.filter(















        rider=request.user,















        status__in=['pending', 'processing', 'send-to-rider', 'out_for_delivery', 'rider_accepted']















    ).select_related('customer', 'customer__profile').prefetch_related('items__product').order_by('created_at')

    return_pickups = ReturnRequest.objects.filter(
        pickup_rider=request.user,
        status='approved',
        pickup_status__in=('assigned', 'picked_up', 'payment_returned'),
    ).select_related(
        'order', 'order__customer', 'order__customer__profile'
    ).order_by('created_at')































    today = timezone.now().date()















    completed_count = Order.objects.filter(















        rider=request.user,















        status='delivered',















        delivered_at__date=today















    ).count()































    pending_count = my_orders.filter(status='pending').count()















    processing_count = my_orders.filter(status='processing').count()















    out_for_delivery_count = my_orders.filter(status='out_for_delivery').count()

    today_earnings = Order.objects.filter(
        rider=request.user,
        status='delivered',
        delivered_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0































    context = {
        'orders': my_orders,
        'return_pickups': return_pickups,















        'completed_count': completed_count,















        'pending_count': pending_count,















        'processing_count': processing_count,















        'out_for_delivery_count': out_for_delivery_count,







        'today_earnings': today_earnings,







        'station_lat': STATION_LAT,















        'station_lng': STATION_LNG,
















        'station_address': STATION_ADDRESS,
        'delivery_base_fee': DELIVERY_BASE_FEE,















    }















    return render(request, 'accounts/rider_dashboard.html', context)















































@rider_required















def rider_delivery_history(request):















    """View for rider to see history of completed deliveries"""















    # Get filter parameters















    date_from = request.GET.get('date_from', '')















    date_to = request.GET.get('date_to', '')















    















    # Base query - all delivered orders for this rider















    delivered_orders = Order.objects.filter(















        rider=request.user,















        status='delivered'















    ).select_related('customer', 'customer__profile').prefetch_related('items__product').order_by('-delivered_at')















    















    # Apply date filters if provided















    if date_from:















        try:















            from datetime import datetime















            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()















            delivered_orders = delivered_orders.filter(delivered_at__date__gte=date_from_obj)















        except ValueError:















            pass















    















    if date_to:















        try:















            from datetime import datetime















            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()















            delivered_orders = delivered_orders.filter(delivered_at__date__lte=date_to_obj)















        except ValueError:















            pass















    















    # Calculate statistics















    total_deliveries = delivered_orders.count()















    total_earnings = delivered_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    















    # Today's stats















    today = timezone.now().date()















    today_deliveries = delivered_orders.filter(delivered_at__date=today).count()















    today_earnings = delivered_orders.filter(delivered_at__date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    















    # This week's stats















    week_start = today - timedelta(days=today.weekday())















    week_deliveries = delivered_orders.filter(delivered_at__date__gte=week_start).count()















    week_earnings = delivered_orders.filter(delivered_at__date__gte=week_start).aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    















    # This month's stats















    month_start = today.replace(day=1)















    month_deliveries = delivered_orders.filter(delivered_at__date__gte=month_start).count()















    month_earnings = delivered_orders.filter(delivered_at__date__gte=month_start).aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    















    context = {















        'delivered_orders': delivered_orders,















        'total_deliveries': total_deliveries,















        'total_earnings': total_earnings,















        'today_deliveries': today_deliveries,















        'today_earnings': today_earnings,















        'week_deliveries': week_deliveries,















        'week_earnings': week_earnings,















        'month_deliveries': month_deliveries,















        'month_earnings': month_earnings,















        'date_from': date_from,















        'date_to': date_to,















    }















    return render(request, 'accounts/rider_delivery_history.html', context)















































# ===================== CUSTOMER DASHBOARD =====================















@customer_required















def customer_dashboard(request):



    from allauth.socialaccount.models import SocialAccount
    from .models import OrderItem



    from django.db.models import Count



    from django.utils import timezone



    import json



    from collections import defaultdict







    recent_orders = Order.objects.filter(



        customer=request.user



    ).prefetch_related('items__product').order_by('-created_at')[:5]







    total_orders = Order.objects.filter(customer=request.user, status='delivered').count()







    popular_products = Product.objects.filter(



        is_active=True,



        stock_quantity__gt=0



    ).annotate(



        total_ordered=Sum('orderitem__quantity')



    ).filter(total_ordered__gt=0).order_by('-total_ordered')[:6]







    if not popular_products:



        popular_products = Product.objects.filter(



            is_active=True,



            stock_quantity__gt=0



        ).order_by('?')[:6]







    # ── Analytics Data ──



    now = timezone.now()







    # This week's orders



    week_start = now - timezone.timedelta(days=now.weekday())



    this_week_orders = Order.objects.filter(



        customer=request.user,



        created_at__gte=week_start



    ).count()







    # This month's orders



    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)



    this_month_orders = Order.objects.filter(



        customer=request.user,



        created_at__gte=month_start



    ).count()







    # This month's spending



    this_month_spent = Order.objects.filter(



        customer=request.user,



        created_at__gte=month_start



    ).aggregate(total=Sum('total_amount'))['total'] or 0







    # Total gallons ordered (count 5-gallon containers)



    total_gallons = OrderItem.objects.filter(



        order__customer=request.user,



        product__name__icontains='gallon'



    ).aggregate(total=Sum('quantity'))['total'] or 0







    # Weekly activity chart data (last 7 days)



    weekly_activity = defaultdict(int)



    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']



    for i in range(7):



        day_date = now - timezone.timedelta(days=i)



        day_name = days[day_date.weekday()]



        count = Order.objects.filter(



            customer=request.user,



            created_at__date=day_date.date()



        ).count()



        weekly_activity[day_name] = count







    # Favorite products (most ordered by this customer)



    favorite_products = OrderItem.objects.filter(



        order__customer=request.user



    ).values('product__name').annotate(



        count=Sum('quantity')



    ).order_by('-count')[:5]







    session_requires_google_profile = (
        request.session.get('google_profile_completion_user_id') == request.user.pk
    )
    show_google_profile_modal = session_requires_google_profile
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.phone_number and profile.address:
            show_google_profile_modal = False
        elif profile and not session_requires_google_profile:
            show_google_profile_modal = SocialAccount.objects.filter(
                user_id=request.user.pk,
                provider='google',
            ).exists()

    context = {



        'recent_orders': recent_orders,



        'total_orders': total_orders,



        'popular_products': popular_products,



        # Analytics



        'this_week_orders': this_week_orders,



        'this_month_orders': this_month_orders,



        'this_month_spent': this_month_spent,



        'total_gallons': total_gallons,



        'weekly_activity': dict(weekly_activity),



        'weekly_activity_json': json.dumps(dict(weekly_activity)),



        'favorite_products': favorite_products,

        'announcements': AdminAnnouncementImage.objects.all(),
        'show_google_profile_modal': show_google_profile_modal,
        'station_lat': STATION_LAT,
        'station_lng': STATION_LNG,

    }



    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
@require_POST
def complete_google_profile(request):
    completion_user_id = request.session.get('google_profile_completion_user_id')
    if completion_user_id is not None and completion_user_id != request.user.pk:
        return JsonResponse({'error': 'Profile completion is not required.'}, status=403)

    if completion_user_id != request.user.pk:
        from allauth.socialaccount.models import SocialAccount

        profile = UserProfile.objects.filter(user=request.user).first()
        has_incomplete_google_profile = (
            SocialAccount.objects.filter(
                user_id=request.user.pk,
                provider='google',
            ).exists()
            and (profile is None or not profile.phone_number or not profile.address)
        )
        if not has_incomplete_google_profile:
            return JsonResponse({'error': 'Profile completion is not required.'}, status=403)

    form = GoogleProfileCompletionForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'customer'},
    )
    profile.phone_number = form.cleaned_data['phone_number']
    profile.address = form.cleaned_data['address']
    profile.default_latitude = form.cleaned_data['default_latitude']
    profile.default_longitude = form.cleaned_data['default_longitude']
    profile.save(update_fields=[
        'phone_number',
        'address',
        'default_latitude',
        'default_longitude',
    ])
    request.user.profile = profile
    Consumer.objects.get_or_create(user=request.user)
    request.session.pop('google_profile_completion_user_id', None)
    return JsonResponse({'success': True})















































@customer_required















def customer_order_detail(request, order_id):















    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id, customer=request.user)















    context = {















        'order': order,















        'station_lat': STATION_LAT,















        'station_lng': STATION_LNG,















        'station_address': STATION_ADDRESS,















    }















    return render(request, 'accounts/customer_order_detail.html', context)















































# ===================== USER MANAGEMENT =====================















@admin_required















def manage_users(request):















    users = User.objects.all().select_related('profile').order_by('-date_joined')















    role_filter = request.GET.get('role', '')















    search_query = request.GET.get('search', '')















    















    if role_filter:















        users = users.filter(profile__role=role_filter)















    















    if search_query:















        users = users.filter(















            Q(first_name__icontains=search_query) |















            Q(last_name__icontains=search_query) |















            Q(email__icontains=search_query)















        )















    















    if request.method == 'POST' and 'create_staff' in request.POST:















        form = StaffUserCreationForm(request.POST)















        if form.is_valid():















            form.save()















            messages.success(request, 'Staff/Rider account created successfully!')















            return redirect('manage_users')















    else:















        form = StaffUserCreationForm()















    















    context = {















        'users': users,















        'form': form,















        'role_filter': role_filter,















        'search_query': search_query,















    }















    return render(request, 'accounts/manage_users.html', context)















































@admin_required















def edit_user(request, user_id):















    user = get_object_or_404(User, id=user_id)















    















    if request.method == 'POST':















        user.username = request.POST.get('username')















        user.email = request.POST.get('email')















        user.first_name = request.POST.get('first_name')















        user.last_name = request.POST.get('last_name')















        user.save()















        user.profile.phone_number = request.POST.get('phone_number')















        user.profile.address = request.POST.get('address')















        user.profile.role = request.POST.get('role')















        user.profile.save()















        messages.success(request, 'User updated successfully!')















        return redirect('manage_users')















    















    return render(request, 'accounts/edit_user.html', {'edit_user': user})















































@admin_required















def delete_user(request, user_id):















    user = get_object_or_404(User, id=user_id)















    if user != request.user:















        user.delete()















        messages.success(request, 'User deleted successfully!')















    else:















        messages.error(request, 'You cannot delete your own account!')















    return redirect('manage_users')















































# ===================== ORDER MANAGEMENT =====================









@staff_required
def return_orders(request):
    return_requests = ReturnRequest.objects.select_related(
        'order',
        'order__customer',
        'reviewed_by',
        'pickup_rider',
        'inspected_by',
    ).prefetch_related(
        'order__items__product',
        'items__order_item__product',
        'evidence_images',
    ).order_by('-created_at')

    status_filter = request.GET.get('status', 'all')
    valid_statuses = {'pending', 'approved', 'rejected'}
    if status_filter in valid_statuses:
        return_requests = return_requests.filter(status=status_filter)
    else:
        status_filter = 'all'

    counts = {
        'all': ReturnRequest.objects.count(),
        'pending': ReturnRequest.objects.filter(status='pending').count(),
        'approved': ReturnRequest.objects.filter(status='approved').count(),
        'rejected': ReturnRequest.objects.filter(status='rejected').count(),
    }
    return_page = Paginator(return_requests, 12).get_page(request.GET.get('page'))
    for return_request in return_page.object_list:
        return_items = list(return_request.items.all())
        return_request.sales_adjustment_total = sum(
            (item.sales_adjustment for item in return_items),
            Decimal('0.00'),
        )
        for return_item in return_items:
            return_item.damaged_quantity = (
                return_item.quantity - (return_item.restockable_quantity or 0)
            )
            return_item.display_return_amount = (
                return_item.sales_adjustment
                if return_request.inspected_at
                else _calculate_return_sales_adjustment(return_request, return_item)
            )
        return_request.return_cash_total = sum(
            (item.display_return_amount for item in return_items),
            Decimal('0.00'),
        )

    context = {
        'return_page': return_page,
        'return_requests': return_page.object_list,
        'return_status_filter': status_filter,
        'return_counts': counts,
        'riders': User.objects.filter(
            profile__role='rider',
            is_active=True,
        ).order_by('first_name', 'username'),
    }
    return render(request, 'accounts/return_orders.html', context)


@staff_required
def manage_orders(request):















    orders = Order.objects.all().select_related(















        'customer', 'customer__profile', 'rider'















    ).prefetch_related(
        'items__product',
        'return_request__items__order_item__product',
        'return_request__evidence_images',
    ).select_related(
        'return_request', 'return_request__pickup_rider'
    ).order_by('-created_at')































    # Filter by status if provided















    status_filter = request.GET.get('status')

    in_progress_statuses = (
        'processing',
        'choose_rider',
        'send-to-rider',
        'rider_accepted',
        'out_for_delivery',
    )

    if status_filter:

        if status_filter == 'return':
            orders = orders.filter(return_request__isnull=False)
        elif status_filter == 'delivered':
            orders = orders.filter(status='delivered', return_request__isnull=True)
        elif status_filter == 'out_for_delivery':
            orders = orders.filter(status__in=in_progress_statuses)
        else:
            orders = orders.filter(status=status_filter)


    tab_counts = Order.objects.aggregate(
        all_orders_count=Count('id'),
        awaiting_payment_count=Count(
            'id',
            filter=Q(status='awaiting_payment'),
        ),
        pending_count=Count('id', filter=Q(status='pending')),
        in_progress_count=Count(
            'id',
            filter=Q(status__in=in_progress_statuses),
        ),
        completed_orders_count=Count(
            'id',
            filter=Q(status='delivered', return_request__isnull=True),
        ),
        return_orders_count=Count(
            'id',
            filter=Q(return_request__isnull=False),
        ),
        cancelled_orders_count=Count('id', filter=Q(status='cancelled')),
    )















    processing_count = orders.filter(status='processing').count()















    out_for_delivery_count = orders.filter(status='out_for_delivery').count()















    delivered_count = orders.filter(status='delivered').count()































    customers = User.objects.filter(profile__role='customer', is_active=True)















    riders = User.objects.filter(profile__role='rider', is_active=True)















    products = Product.objects.filter(is_active=True)































    if request.method == 'POST':















        form = OrderForm(request.POST)















        if form.is_valid():















            order = form.save(commit=False)















            last_order = Order.objects.order_by('-id').first()















            if last_order:















                try:















                    order_num = int(last_order.order_number.split('-')[1]) + 1















                except (ValueError, IndexError):















                    order_num = 1000















            else:















                order_num = 1000















            order.order_number = _next_order_number(exclude_order_id=order.pk)















            order.save()















            messages.success(request, 'Order created successfully!')















            return redirect('manage_orders')















    else:















        form = OrderForm()































    station_availability, _ = StationAvailability.objects.get_or_create(pk=1)
    context = {
        'orders': orders,
        'station_delivery_fee_rates': {
            'up_to_2km': station_availability.delivery_fee_up_to_2km,
            'up_to_3km': station_availability.delivery_fee_up_to_3km,
        },
        'form': form,















        'customers': customers,















        'riders': riders,















        'products': products,

        'all_orders_count': tab_counts['all_orders_count'],
        'awaiting_payment_count': tab_counts['awaiting_payment_count'],
        'pending_count': tab_counts['pending_count'],
        'in_progress_count': tab_counts['in_progress_count'],
        'completed_orders_count': tab_counts['completed_orders_count'],
        'return_orders_count': tab_counts['return_orders_count'],
        'cancelled_orders_count': tab_counts['cancelled_orders_count'],
        'processing_count': processing_count,















        'out_for_delivery_count': out_for_delivery_count,















        'delivered_count': delivered_count,















    }















    return render(request, 'accounts/manage_orders.html', context)















































@staff_required















def update_order_status(request, order_id):















    order = get_object_or_404(Order, id=order_id)















    if request.method == 'POST':















        # Check if this is an AJAX request (JSON content type)















        is_ajax = request.headers.get('Content-Type') == 'application/json'































        # Prevent editing cancelled orders















        if order.status == 'cancelled':















            if is_ajax:















                return JsonResponse({'success': False, 'error': 'Order is cancelled and cannot be edited'}, status=400)















            messages.error(request, f'Order #{order.order_number} is cancelled and cannot be edited.')















            status_filter = request.POST.get('status_filter')















            if status_filter:















                return redirect(f'{reverse("manage_orders")}?status={status_filter}')















            return redirect('manage_orders')































        if is_ajax:















            # Parse JSON body for AJAX requests















            try:















                data = json.loads(request.body)















                new_status = data.get('status')















                rider_id = None















            except json.JSONDecodeError:















                return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)















        else:















            # Regular form submission















            new_status = request.POST.get('status')







            rider_id = request.POST.get('rider_id', '').strip()

        if (
            order.status == 'out_for_delivery'
            and rider_id
            and str(order.rider_id) != rider_id
        ):
            error = 'The rider cannot be changed after the order is On the Way.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error}, status=400)
            messages.error(request, error)
            return redirect('manage_orders')

        if order.status == 'awaiting_payment' and (
            order.payment_method != 'gcash'
            or new_status != 'pending'
            or rider_id
        ):
            error = 'Confirm GCash payment before processing or assigning this order.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error}, status=400)
            messages.error(request, error)
            return redirect(f'{reverse("manage_orders")}?status=awaiting_payment')

        if new_status == 'choose_rider' and order.status not in {
            'processing',
            'choose_rider',
        }:
            error = 'Set the order to Processing before choosing a rider.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error}, status=400)
            messages.error(request, error)
            return redirect('manage_orders')




        # If rider is being assigned, automatically set status to send-to-rider















        if rider_id:















            try:















                rider = User.objects.get(id=rider_id, profile__role='rider')















                order.rider = rider















                order.status = 'send-to-rider'















            except User.DoesNotExist:















                pass















        elif new_status:















            order.status = new_status































        # Check if status is being changed to delivered















        old_status = order.status















        if new_status == 'delivered' or (rider_id and order.status == 'send-to-rider' and old_status != 'delivered'):















            # This will be handled after save if new_status is delivered















            pass































        order.save()































        # If status changed to delivered, create a Sale in POS















        if new_status == 'delivered' and old_status != 'delivered':















            from .models import OrderItem















            # Check if a sale already exists for this order















            existing_sale = Sale.objects.filter(order_number=order.order_number).first()
            if existing_sale and existing_sale.created_at < order.created_at:
                existing_sale.order_number = (
                    f'{order.order_number}-LEGACY-{existing_sale.pk}'
                )
                existing_sale.save(update_fields=['order_number'])
                existing_sale = None















            if not existing_sale:















                # Convert payment method















                payment_method = 'cash' if order.payment_method == 'cod' else order.payment_method















                















                # Create the sale















                sale = Sale.objects.create(















                    customer=order.customer,















                    cashier=order.rider or request.user,  # Use rider or current user as cashier















                    total_amount=order.total_amount,















                    payment_method=payment_method,















                    status='completed',















                    order_type='delivery',















                    order_number=order.order_number  # Link to original order















                )































                # Create sale items from order items















                for order_item in order.items.all():















                    SaleItem.objects.create(















                        sale=sale,
                        product=order_item.product,
                        order_item=order_item,
                        quantity=order_item.quantity,















                        unit_price=order_item.unit_price,















                        subtotal=order_item.subtotal















                    )































        if is_ajax:















            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': (
                    'On the Way'
                    if order.status == 'out_for_delivery'
                    else order.get_status_display()
                ),
            })































        messages.success(request, f'Order #{order.order_number} updated to {order.get_status_display()}.')































        # Preserve filter status in redirect















        status_filter = request.POST.get('status_filter')















        if status_filter:















            from django.urls import reverse















            return redirect(f'{reverse("manage_orders")}?status={status_filter}')















    return redirect('manage_orders')















































# ===================== CUSTOMER ORDERS =====================















@customer_required















def customer_order_page(request):

    products = Product.objects.filter(is_active=True).order_by('name')
    try:
        station_availability, _ = StationAvailability.objects.get_or_create(pk=1)
        delivery_fee_rates = {
            'up_to_2km': station_availability.delivery_fee_up_to_2km,
            'up_to_3km': station_availability.delivery_fee_up_to_3km,
        }
    except (DatabaseError, AttributeError):
        delivery_fee_rates = {
            'up_to_2km': DEFAULT_DELIVERY_FEE_RATES['up_to_2km'],
            'up_to_3km': DEFAULT_DELIVERY_FEE_RATES['up_to_3km'],
        }

    context = {















        'products': products,















        'customer': request.user,















        'station_lat': STATION_LAT,















        'station_lng': STATION_LNG,















        'station_address': STATION_ADDRESS,
        'delivery_fee_rates': delivery_fee_rates,
        'delivery_base_fee': delivery_fee_rates['up_to_2km'],















    }















    return render(request, 'accounts/customer_order.html', context)


@login_required
@require_http_methods(['GET'])
def private_media(request, path):
    profile = getattr(request.user, 'profile', None)
    is_staff = (
        getattr(request.user, 'is_superuser', False)
        or getattr(profile, 'role', None) in {'admin', 'staff'}
    )
    media = None

    order = Order.objects.filter(payment_proof=path).first()
    if order and order.payment_proof:
        if not is_staff:
            raise Http404
        media = order.payment_proof
    else:
        order = Order.objects.filter(delivery_image=path).first()
        if order and order.delivery_image:
            if not is_staff and request.user.pk not in {
                order.customer_id,
                order.rider_id,
            }:
                raise Http404
            media = order.delivery_image

    if media is None:
        return_request = ReturnRequest.objects.filter(
            evidence_image=path,
        ).select_related('order').first()
        if return_request and return_request.evidence_image:
            if not is_staff and request.user.pk not in {
                return_request.order.customer_id,
                return_request.order.rider_id,
                return_request.pickup_rider_id,
            }:
                raise Http404
            media = return_request.evidence_image
        else:
            evidence = ReturnRequestImage.objects.filter(
                image=path,
            ).select_related('return_request__order').first()
            if evidence:
                return_request = evidence.return_request
                if not is_staff and request.user.pk not in {
                    return_request.order.customer_id,
                    return_request.order.rider_id,
                    return_request.pickup_rider_id,
                }:
                    raise Http404
                media = evidence.image

    if media is None:
        product_image = ProductImage.objects.filter(image=path).first()
        if product_image:
            media = product_image.image
        else:
            announcement_image = AdminAnnouncementImage.objects.filter(
                image=path,
            ).first()
            if announcement_image:
                media = announcement_image.image

    if media is None:
        report_photo = MaintenanceReportPhoto.objects.filter(
            image=path,
        ).first()
        if report_photo:
            if not is_staff:
                raise Http404
            media = report_photo.image
        else:
            report = MaintenanceReport.objects.filter(photo=path).first()
            if not report or not report.photo or not is_staff:
                raise Http404
            media = report.photo

    try:
        proof = media.open('rb')
    except FileNotFoundError as exc:
        raise Http404 from exc

    content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    response = FileResponse(proof, content_type=content_type)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response















































@customer_required















@require_POST















def customer_place_order(request):















    from .models import OrderItem















    















    # Get cart items from JSON















    cart_data = request.POST.get('cart_items')















    if not cart_data:















        messages.error(request, 'Cart is empty!')















        return redirect('customer_order')















    















    try:















        cart_items = json.loads(cart_data)















    except json.JSONDecodeError:















        messages.error(request, 'Invalid cart data!')















        return redirect('customer_order')















    















    if not cart_items:















        messages.error(request, 'Cart is empty!')















        return redirect('customer_order')















    















    notes = request.POST.get('notes', '')















    payment_method = request.POST.get('payment_method', 'cod')
    payment_proof = request.FILES.get('payment_proof')

    if payment_method == 'gcash' and not payment_proof:
        messages.error(request, 'Please upload your GCash proof of payment.')
        return redirect('customer_order')































    delivery_address = request.POST.get('delivery_address', '').strip() or request.user.profile.address















    delivery_lat = request.POST.get('delivery_lat', '').strip()















    delivery_lng = request.POST.get('delivery_lng', '').strip()































    try:















        delivery_lat = float(delivery_lat) if delivery_lat else None















        delivery_lng = float(delivery_lng) if delivery_lng else None















    except (ValueError, TypeError):
        delivery_lat = None
        delivery_lng = None

    if delivery_lat is None:
        delivery_lat = request.user.profile.default_latitude
    if delivery_lng is None:
        delivery_lng = request.user.profile.default_longitude

    if (
        delivery_lat is not None
        and delivery_lng is not None
        and not is_within_service_area(delivery_lat, delivery_lng)
    ):
        messages.error(
            request,
            'Our water station only serves Bacoor, Cavite and Las Piñas City.',
        )
        return redirect('customer_order')































    # Recalculate prices and delivery fee on the server so displayed totals
    # cannot be altered by client-side cart data.















    subtotal = Decimal('0.00')
    priced_cart_items = []
    for item in cart_items:
        product = get_object_or_404(Product, id=item['id'])
        quantity = int(item['quantity'])
        if quantity < 1 or (
            product.product_type == 'gallon' and quantity > product.stock_quantity
        ):
            messages.error(request, f'Invalid quantity for {product.name}.')
            return redirect('customer_order')
        subtotal += product.price * quantity
        priced_cart_items.append((product, quantity))

    discount = calculate_buy_ten_get_one_discount(priced_cart_items)
    station_availability, _ = StationAvailability.objects.get_or_create(pk=1)
    delivery_fee_rates = {
        'up_to_2km': station_availability.delivery_fee_up_to_2km,
        'up_to_3km': station_availability.delivery_fee_up_to_3km,
    }
    delivery_fee, delivery_distance_km, delivery_area, delivery_fee_requires_approval = calculate_delivery_fee(
        delivery_lat, delivery_lng, delivery_address, delivery_fee_rates
    )
    total_amount = subtotal - discount + delivery_fee































    last_order = Order.objects.order_by('-id').first()















    if last_order:















        try:















            order_num = int(last_order.order_number.split('-')[1]) + 1















        except (ValueError, IndexError):















            order_num = 1000















    else:















        order_num = 1000















    order_number = _next_order_number()































    status = 'awaiting_payment' if payment_method == 'gcash' else 'pending'































    # Create order without product/quantity (now in OrderItem)















    order = Order.objects.create(















        customer=request.user,















        order_number=order_number,
        subtotal=subtotal,
        discount=discount,
        delivery_fee=delivery_fee,
        delivery_distance_km=delivery_distance_km,
        delivery_area=delivery_area,
        delivery_fee_requires_approval=delivery_fee_requires_approval,
        total_amount=total_amount,















        delivery_address=delivery_address,















        notes=notes,















        status=status,















        payment_method=payment_method,
        payment_proof=payment_proof,















        delivery_lat=delivery_lat,















        delivery_lng=delivery_lng,















    )































    # Create order items















    for item in cart_items:















        product = get_object_or_404(Product, id=item['id'])















        OrderItem.objects.create(















            order=order,















            product=product,















            quantity=item['quantity'],















            unit_price=product.price,















            subtotal=product.price * item['quantity']















        )































    if delivery_lat and delivery_lng:















        try:















            request.user.profile.default_latitude = delivery_lat















            request.user.profile.default_longitude = delivery_lng















            request.user.profile.save()















        except Exception as e:















            print(f"Error saving default location to profile: {e}")































    consumer, _ = Consumer.objects.get_or_create(user=request.user)















    consumer.total_orders += 1















    consumer.last_order_date = timezone.now()















    consumer.save()































    messages.success(request, f'Order #{order_number} placed successfully!')















    return redirect('customer_orders')















































@customer_required















def customer_orders(request):















    orders = Order.objects.filter(customer=request.user).select_related(















        'rider', 'rider__profile'















    ).prefetch_related(
        'items__product',
        'return_request__items__order_item__product',
    ).select_related(
        'return_request', 'return_request__pickup_rider'
    ).order_by('-created_at')
    for order in orders:
        if hasattr(order, 'return_request'):
            order.return_request.sales_adjustment_total = sum(
                (item.sales_adjustment for item in order.return_request.items.all()),
                Decimal('0.00'),
            )

    context = {















        'orders': orders,















        'station_lat': STATION_LAT,















        'station_lng': STATION_LNG,















        'station_address': STATION_ADDRESS,















    }















    return render(request, 'accounts/customer_orders.html', context)


def _calculate_return_sales_adjustment(return_request, return_item):
    order_item = return_item.order_item
    item_total = order_item.unit_price * return_item.quantity
    discount_share = Decimal('0.00')
    if return_request.order.subtotal > 0:
        discount_share = (
            return_request.order.discount
            * order_item.subtotal
            / return_request.order.subtotal
            * return_item.quantity
            / order_item.quantity
        )
    return max(
        Decimal('0.00'),
        (item_total - discount_share).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
    )


@customer_required
def customer_returns(request):
    return_requests = list(
        ReturnRequest.objects.filter(order__customer=request.user)
        .select_related('order', 'pickup_rider', 'inspected_by')
        .prefetch_related('items__order_item__product')
        .order_by('-updated_at', '-id')
    )
    for return_request in return_requests:
        return_items = list(return_request.items.all())
        return_request.sales_adjustment_total = sum(
            (item.sales_adjustment for item in return_items),
            Decimal('0.00'),
        )
        for item in return_items:
            item.display_return_amount = (
                item.sales_adjustment
                if return_request.inspected_at
                else _calculate_return_sales_adjustment(return_request, item)
            )
        return_request.return_cash_total = sum(
            (item.display_return_amount for item in return_items),
            Decimal('0.00'),
        )
        return_request.net_total_amount = return_request.order.total_amount
        if return_request.inspected_at:
            return_request.net_total_amount = max(
                Decimal('0.00'),
                return_request.order.total_amount - return_request.sales_adjustment_total,
            )

    return render(request, 'accounts/customer_returns.html', {
        'return_requests': return_requests,
    })


@login_required
@require_POST
def create_return_request(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user,
        status='delivered',
    )
    delivery_date = order.delivered_at or order.updated_at
    if timezone.now() > delivery_date + timedelta(days=3):
        return JsonResponse(
            {'error': 'Return requests must be submitted within 3 days of delivery.'},
            status=400,
        )

    if hasattr(order, 'return_request'):
        return JsonResponse(
            {
                'error': 'A return request already exists for this order.',
                'status': order.return_request.status,
            },
            status=409,
        )

    try:
        selected_items = json.loads(request.POST.get('items', '[]'))
    except (TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Select the order items and quantities to return.'}, status=400)
    if not isinstance(selected_items, list) or not selected_items:
        return JsonResponse({'error': 'Select at least one item to return.'}, status=400)
    requested_quantities = {}
    for selected_item in selected_items:
        if not isinstance(selected_item, dict):
            return JsonResponse({'error': 'Invalid returned item selection.'}, status=400)
        item_id = selected_item.get('order_item_id')
        quantity = selected_item.get('quantity')
        if isinstance(item_id, str) and item_id.isdigit():
            item_id = int(item_id)
        if isinstance(quantity, str) and quantity.isdigit():
            quantity = int(quantity)
        if (
            not isinstance(item_id, int) or isinstance(item_id, bool)
            or not isinstance(quantity, int) or isinstance(quantity, bool)
            or quantity < 1 or item_id in requested_quantities
        ):
            return JsonResponse({'error': 'Each returned item must have a valid quantity.'}, status=400)
        requested_quantities[item_id] = quantity
    order_items = {
        item.id: item
        for item in OrderItem.objects.filter(
            order_id=order.id,
            id__in=requested_quantities,
        ).select_related('product')
    }
    if len(order_items) != len(requested_quantities):
        return JsonResponse({'error': 'A selected item does not belong to this order.'}, status=400)
    for item_id, quantity in requested_quantities.items():
        if quantity > order_items[item_id].quantity:
            return JsonResponse(
                {'error': f"Return quantity for {order_items[item_id].product.name} exceeds the purchased quantity."},
                status=400,
            )

    reason = request.POST.get('reason')
    details = request.POST.get('details', '').strip()
    uploaded_images = request.FILES.getlist('evidence_images')
    if not uploaded_images:
        uploaded_images = request.FILES.getlist('evidence_image')
    valid_reasons = {choice[0] for choice in ReturnRequest.REASON_CHOICES}
    if reason not in valid_reasons:
        return JsonResponse({'error': 'Please select a valid return reason.'}, status=400)
    if reason == 'other' and not details:
        return JsonResponse({'error': 'Please provide details for the return request.'}, status=400)
    if not uploaded_images:
        return JsonResponse({'error': 'Please upload at least one photo showing the item or issue.'}, status=400)
    for uploaded_image in uploaded_images:
        if not uploaded_image.content_type.startswith('image/'):
            return JsonResponse({'error': 'Every evidence file must be an image.'}, status=400)
        if uploaded_image.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'Each evidence image must be 5 MB or smaller.'}, status=400)
        try:
            image = Image.open(uploaded_image)
            image.verify()
            uploaded_image.seek(0)
        except (UnidentifiedImageError, OSError):
            return JsonResponse({'error': 'One of the uploaded files is not a valid image.'}, status=400)

    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update(),
            id=order_id,
            customer=request.user,
            status='delivered',
        )
        if ReturnRequest.objects.filter(order=order).exists():
            return JsonResponse(
                {'error': 'A return request already exists for this order.'},
                status=409,
            )
        return_request = ReturnRequest.objects.create(
            order=order,
            reason=reason,
            details=details,
        )
        ReturnRequestItem.objects.bulk_create([
            ReturnRequestItem(
                return_request_id=return_request.id,
                order_item_id=order_items[item_id].id,
                quantity=quantity,
            )
            for item_id, quantity in requested_quantities.items()
        ])
        for uploaded_image in uploaded_images:
            ReturnRequestImage.objects.create(
                return_request=return_request,
                image=uploaded_image,
            )
    admin_staff = User.objects.filter(profile__role__in=('admin', 'staff'))
    Notification.objects.bulk_create([
        Notification(
            recipient=recipient,
            title='New return request',
            description=f'Order {order.order_number} has a return request for {return_request.get_reason_display().lower()}.',
            category='orders',
            severity='warning',
            target_url=reverse('return_orders'),
        )
        for recipient in admin_staff
    ])
    return JsonResponse({
        'ok': True,
        'status': return_request.status,
        'status_label': return_request.get_status_display(),
    }, status=201)


@login_required
@require_POST
def review_return_request(request, return_request_id):
    if request.user.profile.role not in ('admin', 'staff'):
        return JsonResponse({'error': 'Unauthorized.'}, status=403)
    return_request = get_object_or_404(
        ReturnRequest.objects.select_related('order'),
        id=return_request_id,
    )
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data.'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Invalid request data.'}, status=400)
    action = payload.get('action')
    if action not in ('approve', 'reject'):
        return JsonResponse({'error': 'Invalid review action.'}, status=400)
    if return_request.status != 'pending':
        return JsonResponse({'error': 'This return request has already been reviewed.'}, status=409)

    review_notes = payload.get('notes', '')
    if not isinstance(review_notes, str):
        return JsonResponse({'error': 'Review notes must be text.'}, status=400)
    review_notes = review_notes.strip()
    if len(review_notes) > 2000:
        return JsonResponse({'error': 'Review notes must be 2,000 characters or fewer.'}, status=400)
    if action == 'reject' and not review_notes:
        return JsonResponse({'error': 'Please provide a reason for rejecting the return request.'}, status=400)

    rider_id = payload.get('rider_id')
    pickup_rider = None
    if action == 'approve':
        if rider_id in (None, ''):
            return JsonResponse({'error': 'Select an active rider to approve this return request.'}, status=400)
        if isinstance(rider_id, str) and rider_id.isdigit():
            rider_id = int(rider_id)
        if not isinstance(rider_id, int) or isinstance(rider_id, bool):
            return JsonResponse({'error': 'Select an active rider.'}, status=400)
        pickup_rider = User.objects.filter(
            id=rider_id,
            profile__role='rider',
            is_active=True,
        ).first()
        if pickup_rider is None:
            return JsonResponse({'error': 'The selected rider is unavailable.'}, status=400)
    elif rider_id not in (None, ''):
        return JsonResponse({'error': 'A rider can only be assigned when approving a return request.'}, status=400)

    return_request.status = 'approved' if action == 'approve' else 'rejected'
    return_request.pickup_status = (
        'assigned'
        if action == 'approve'
        else 'not_ready'
    )
    return_request.pickup_rider = pickup_rider
    return_request.review_notes = review_notes
    return_request.reviewed_by = request.user
    return_request.reviewed_at = timezone.now()
    return_request.save(update_fields=[
        'status',
        'pickup_status',
        'pickup_rider',
        'review_notes',
        'reviewed_by',
        'reviewed_at',
        'updated_at',
    ])
    decision_text = 'approved' if action == 'approve' else 'rejected'
    notification_description = (
        f'Return request for order {return_request.order.order_number} was {decision_text}.'
    )
    if review_notes:
        notification_description += f' Staff note: {review_notes}'
    if action == 'approve' and pickup_rider:
        notification_description += (
            ' A rider has been assigned to pick up the returned product.'
        )
    elif action == 'approve':
        notification_description += ' The station will arrange a rider pickup and notify you once assigned.'
    Notification.objects.create(
        recipient=return_request.order.customer,
        title='Return request updated',
        description=notification_description,
        category='orders',
        severity='info' if action == 'approve' else 'warning',
        target_url=reverse('customer_returns'),
    )
    if pickup_rider:
        Notification.objects.create(
            recipient=pickup_rider,
            title='Return pickup assigned',
            description=f'Pick up the returned product for order {return_request.order.order_number}.',
            category='orders',
            severity='warning',
            target_url=reverse('rider_dashboard'),
        )
    return JsonResponse({
        'ok': True,
        'status': return_request.status,
        'status_label': return_request.get_status_display(),
        'pickup_status': return_request.pickup_status,
        'notes': return_request.review_notes,
    })


@login_required
@require_POST
def assign_return_pickup(request, return_request_id):
    if request.user.profile.role not in ('admin', 'staff'):
        return JsonResponse({'error': 'Unauthorized.'}, status=403)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data.'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Invalid request data.'}, status=400)

    rider_id = payload.get('rider_id')
    if isinstance(rider_id, str) and rider_id.isdigit():
        rider_id = int(rider_id)
    if not isinstance(rider_id, int) or isinstance(rider_id, bool):
        return JsonResponse({'error': 'Select an active rider.'}, status=400)

    rider = User.objects.filter(
        id=rider_id,
        profile__role='rider',
        is_active=True,
    ).first()
    if rider is None:
        return JsonResponse({'error': 'The selected rider is unavailable.'}, status=400)

    with transaction.atomic():
        return_request = get_object_or_404(
            ReturnRequest.objects.select_for_update().select_related('order'),
            id=return_request_id,
        )
        if return_request.status != 'approved':
            return JsonResponse(
                {'error': 'Only approved return requests can be assigned for pickup.'},
                status=409,
            )
        if return_request.pickup_status != 'awaiting_assignment':
            return JsonResponse(
                {'error': 'This return pickup has already been assigned or completed.'},
                status=409,
            )

        return_request.pickup_rider = rider
        return_request.pickup_status = 'assigned'
        return_request.save(update_fields=[
            'pickup_rider',
            'pickup_status',
            'updated_at',
        ])
        Notification.objects.bulk_create([
            Notification(
                recipient=rider,
                title='Return pickup assigned',
                description=f'Pick up the returned product for order {return_request.order.order_number}.',
                category='orders',
                severity='warning',
                target_url=reverse('rider_dashboard'),
            ),
            Notification(
                recipient=return_request.order.customer,
                title='Return pickup arranged',
                description=f'A rider has been assigned to pick up the returned product for order {return_request.order.order_number}.',
                category='orders',
                severity='info',
                target_url=reverse('customer_returns'),
            ),
        ])

    return JsonResponse({
        'ok': True,
        'pickup_status': return_request.pickup_status,
        'pickup_status_label': return_request.get_pickup_status_display(),
        'rider_name': rider.get_full_name() or rider.username,
    })


@rider_required
@require_POST
def update_return_pickup_status(request, return_request_id):
    if request.user.profile.role != 'rider':
        return JsonResponse({'error': 'Unauthorized.'}, status=403)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data.'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Invalid request data.'}, status=400)

    action = payload.get('action')
    allowed_transitions = {
        'picked_up': ('assigned',),
        'payment_returned': ('picked_up',),
        'received': ('payment_returned',),
    }
    if action not in allowed_transitions:
        return JsonResponse({'error': 'Invalid pickup status.'}, status=400)

    with transaction.atomic():
        return_request = get_object_or_404(
            ReturnRequest.objects.select_for_update().select_related('order'),
            id=return_request_id,
            pickup_rider=request.user,
            status='approved',
        )
        if return_request.pickup_status not in allowed_transitions[action]:
            return JsonResponse(
                {'error': 'This pickup step is not available yet.'},
                status=409,
            )

        return_request.pickup_status = action
        update_fields = ['pickup_status', 'updated_at']
        if action == 'picked_up':
            return_request.picked_up_at = timezone.now()
            update_fields.append('picked_up_at')
            title = 'Return product picked up'
            description = (
                f'The rider picked up the returned product for order '
                f'{return_request.order.order_number}.'
            )
        elif action == 'payment_returned':
            return_request.payment_returned_at = timezone.now()
            update_fields.append('payment_returned_at')
            title = 'Return payment marked as returned'
            description = (
                f'The rider marked the return payment for order '
                f'{return_request.order.order_number} as returned.'
            )
        else:
            return_request.received_at = timezone.now()
            update_fields.append('received_at')
            title = 'Return product received by station'
            description = (
                f'The returned product for order {return_request.order.order_number} '
                'has been brought back to the station.'
            )
        return_request.save(update_fields=update_fields)
        Notification.objects.create(
            recipient=return_request.order.customer,
            title=title,
            description=description,
            category='orders',
            severity='info',
            target_url=reverse('customer_returns'),
        )
        if action == 'received':
            Notification.objects.bulk_create([
                Notification(
                    recipient=recipient,
                    title='Returned product received at station',
                    description=(
                        f'The rider returned the product for order '
                        f'{return_request.order.order_number} to the station.'
                    ),
                    category='orders',
                    severity='info',
                    target_url=reverse('return_orders'),
                )
                for recipient in User.objects.filter(
                    profile__role__in=('admin', 'staff')
                )
            ])

    return JsonResponse({
        'ok': True,
        'pickup_status': return_request.pickup_status,
        'pickup_status_label': return_request.get_pickup_status_display(),
    })


@login_required
@require_POST
def inspect_return_request(request, return_request_id):
    if request.user.profile.role not in ('admin', 'staff'):
        return JsonResponse({'error': 'Unauthorized.'}, status=403)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data.'}, status=400)
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        return JsonResponse({'error': 'Return inspection items are required.'}, status=400)

    inspections = {}
    for item in payload['items']:
        if not isinstance(item, dict):
            return JsonResponse({'error': 'Invalid return inspection item.'}, status=400)
        item_id = item.get('id')
        restockable_quantity = item.get('restockable_quantity')
        if isinstance(item_id, str) and item_id.isdigit():
            item_id = int(item_id)
        if isinstance(restockable_quantity, str) and restockable_quantity.isdigit():
            restockable_quantity = int(restockable_quantity)
        if (
            not isinstance(item_id, int) or isinstance(item_id, bool)
            or not isinstance(restockable_quantity, int)
            or isinstance(restockable_quantity, bool)
            or restockable_quantity < 0
            or item_id in inspections
        ):
            return JsonResponse({'error': 'Choose a valid restockable quantity for every returned item.'}, status=400)
        inspections[item_id] = restockable_quantity

    with transaction.atomic():
        return_request = get_object_or_404(
            ReturnRequest.objects.select_for_update().select_related('order'),
            id=return_request_id,
            status='approved',
            pickup_status='received',
        )
        if return_request.inspected_at:
            return JsonResponse({'error': 'This return has already been inspected.'}, status=409)

        return_items = list(
            ReturnRequestItem.objects.select_for_update()
            .filter(return_request=return_request)
            .select_related('order_item__product')
        )
        gallon_return_items = [
            item for item in return_items
            if item.order_item.product.product_type == 'gallon'
        ]
        if not return_items or set(inspections) != {item.id for item in gallon_return_items}:
            return JsonResponse({'error': 'Enter a restockable quantity for every returned Water Gallon item.'}, status=400)
        if any(inspections[item.id] > item.quantity for item in gallon_return_items):
            return JsonResponse({'error': 'Restockable quantity cannot exceed the returned quantity.'}, status=400)

        total_adjustment = Decimal('0.00')
        total_restocked_quantity = 0
        for return_item in return_items:
            order_item = return_item.order_item
            restockable_quantity = inspections.get(return_item.id, 0)
            sales_adjustment = _calculate_return_sales_adjustment(
                return_request,
                return_item,
            )
            return_item.restockable_quantity = restockable_quantity
            return_item.sales_adjustment = sales_adjustment
            return_item.save(update_fields=['restockable_quantity', 'sales_adjustment'])
            total_adjustment += sales_adjustment

            sale_item = SaleItem.objects.filter(order_item=order_item).first()
            if sale_item:
                sale_item.returned_quantity += return_item.quantity
                sale_item.returned_amount += sales_adjustment
                sale_item.save(update_fields=['returned_quantity', 'returned_amount'])

            if restockable_quantity and order_item.product.product_type == 'gallon':
                product = Product.objects.select_for_update().get(id=order_item.product_id)
                previous_stock = product.stock_quantity
                product.stock_quantity += restockable_quantity
                product.save(update_fields=['stock_quantity', 'updated_at'])
                total_restocked_quantity += restockable_quantity
                InventoryTransaction.objects.create(
                    product=product,
                    transaction_type='return',
                    quantity=restockable_quantity,
                    previous_stock=previous_stock,
                    new_stock=product.stock_quantity,
                    reference=f'Return for order {return_request.order.order_number}',
                    notes=(
                        f'{restockable_quantity} of {return_item.quantity} returned '
                        f'{product.name} unit(s) passed inspection and were restocked.'
                    ),
                    created_by=request.user,
                )

        sale = Sale.objects.filter(order_number=return_request.order.order_number).first()
        if sale:
            sale.returned_amount += total_adjustment
            sale.save(update_fields=['returned_amount', 'updated_at'])

        return_request.inspected_by = request.user
        return_request.inspected_at = timezone.now()
        return_request.save(update_fields=['inspected_by', 'inspected_at', 'updated_at'])

        Notification.objects.create(
            recipient=return_request.order.customer,
            title='Returned items inspected',
            description=(
                f'The returned items for order {return_request.order.order_number} were inspected. '
                f'The recorded sales adjustment is ₱{total_adjustment:.2f}. '
                'This records the amount only; the payment refund must be processed separately.'
            ),
            category='orders',
            severity='info',
            target_url=reverse('customer_returns'),
        )

    return JsonResponse({
        'ok': True,
        'inspected': True,
        'sales_adjustment': f'{total_adjustment:.2f}',
        'restocked_quantity': total_restocked_quantity,
    })















































@customer_required















def cancel_order(request, order_id):















    order = get_object_or_404(Order, id=order_id, customer=request.user)















    















    if order.status == 'pending':















        order.status = 'cancelled'















        order.save()















        messages.success(request, f'Order #{order.order_number} has been cancelled successfully.')















    elif order.status == 'out_for_delivery':















        messages.error(request, 'Cannot cancel order: Order is already out for delivery.')















    elif order.status == 'delivered':















        messages.error(request, 'Cannot cancel order: Order has already been delivered.')















    elif order.status == 'cancelled':















        messages.info(request, 'Order has already been cancelled.')















    else:















        messages.error(request, 'Cannot cancel order: Order is being processed.')















    















    return redirect('customer_order_detail', order_id=order.id)















































# ===================== CUSTOMER PROFILE =====================















@role_required(['admin', 'staff', 'rider', 'customer'])
@xframe_options_sameorigin
def customer_profile(request):

    profile_route = (
        'customer_profile'
        if request.user.profile.role == 'customer'
        else 'account_profile'
    )
    floating_profile = request.GET.get('floating') == '1'
    profile_redirect = (
        f'{profile_route}?floating=1' if floating_profile else profile_route
    )















    if request.method == 'POST':







        # Update profile info







        request.user.first_name = request.POST.get('first_name')







        request.user.last_name = request.POST.get('last_name')







        request.user.email = request.POST.get('email')







        request.user.save()















        request.user.profile.phone_number = request.POST.get('phone_number')







        request.user.profile.address = request.POST.get('address')







        request.user.profile.save()















        # Handle password change if provided







        current_password = request.POST.get('current_password')







        new_password = request.POST.get('new_password')







        confirm_password = request.POST.get('confirm_password')















        if current_password or new_password or confirm_password:







            # Validate current password







            if not request.user.check_password(current_password):







                messages.error(request, 'Current password is incorrect.')







                return redirect(profile_redirect)















            # Validate new password







            if new_password != confirm_password:







                messages.error(request, 'New password and confirmation do not match.')







                return redirect(profile_redirect)















            if len(new_password) < 8:







                messages.error(request, 'New password must be at least 8 characters.')







                return redirect(profile_redirect)















            # Change password







            request.user.set_password(new_password)







            request.user.save()















            # Re-authenticate user after password change







            from django.contrib.auth import update_session_auth_hash







            update_session_auth_hash(request, request.user)















            messages.success(request, 'Profile and password updated successfully!')







        else:







            messages.success(request, 'Profile updated successfully!')















        return redirect(profile_redirect)















    















    context = {
        'user': request.user,
        'profile_route': profile_route,
        'floating_profile': floating_profile,
        'show_customer_stats': request.user.profile.role == 'customer',
    }

    if context['show_customer_stats']:
        now = timezone.localtime()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        delivered_orders = Order.objects.filter(customer=request.user, status='delivered')
        this_month_orders = delivered_orders.filter(
            created_at__gte=current_month_start,
            created_at__lt=now,
        )
        previous_month_orders = delivered_orders.filter(
            created_at__gte=previous_month_start,
            created_at__lt=current_month_start,
        )

        total_orders = delivered_orders.count()
        total_spent = delivered_orders.aggregate(
            Sum('total_amount')
        )['total_amount__sum'] or Decimal('0.00')
        this_month_order_count = this_month_orders.count()
        previous_month_order_count = previous_month_orders.count()
        this_month_spent = this_month_orders.aggregate(
            Sum('total_amount')
        )['total_amount__sum'] or Decimal('0.00')
        previous_month_spent = previous_month_orders.aggregate(
            Sum('total_amount')
        )['total_amount__sum'] or Decimal('0.00')

        order_change = this_month_order_count - previous_month_order_count
        if order_change > 0:
            order_trend_text = f'+{order_change} this month vs last month'
            order_trend_direction = 'up'
        elif order_change < 0:
            order_trend_text = f'{abs(order_change)} fewer this month'
            order_trend_direction = 'down'
        else:
            order_trend_text = 'Same as last month'
            order_trend_direction = 'same'

        if previous_month_spent > 0:
            spending_change_percent = (
                (this_month_spent - previous_month_spent) * Decimal('100') / previous_month_spent
            ).quantize(Decimal('0.1'))
            if spending_change_percent > 0:
                spending_trend_text = f'+{spending_change_percent}% this month vs last month'
                spending_trend_direction = 'up'
            elif spending_change_percent < 0:
                spending_trend_text = f'{abs(spending_change_percent)}% lower than last month'
                spending_trend_direction = 'down'
            else:
                spending_trend_text = 'Same as last month'
                spending_trend_direction = 'same'
        elif this_month_spent > 0:
            spending_trend_text = 'New spending this month'
            spending_trend_direction = 'up'
        else:
            spending_trend_text = 'Same as last month'
            spending_trend_direction = 'same'

        context.update({
            'total_orders': total_orders,
            'order_trend_text': order_trend_text,
            'order_trend_direction': order_trend_direction,
            'total_spent': f'₱{total_spent:,.2f}',
            'spending_trend_text': spending_trend_text,
            'spending_trend_direction': spending_trend_direction,
            'member_since': request.user.date_joined.strftime('%b %Y'),
        })

    return render(request, 'accounts/customer_profile.html', context)


@role_required(['admin', 'staff', 'rider'])
@xframe_options_sameorigin
def account_profile(request):
    return customer_profile(request)















































# ===================== API for order details =====================

@staff_required
@require_POST
def update_order_delivery_fee(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON request.'}, status=400)

    rate_fields = {
        'up_to_2km': 'delivery_fee_up_to_2km',
        'up_to_3km': 'delivery_fee_up_to_3km',
    }
    if not isinstance(payload, dict) or set(payload) != set(rate_fields):
        return JsonResponse({'success': False, 'error': 'Both distance-based delivery fees are required.'}, status=400)

    fee_rates = {}
    for tier in rate_fields:
        raw_fee = payload[tier]
        if isinstance(raw_fee, bool):
            return JsonResponse({'success': False, 'error': f'Enter a valid fee for {tier}.'}, status=400)
        try:
            fee = Decimal(str(raw_fee))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({'success': False, 'error': f'Enter a valid fee for {tier}.'}, status=400)

        if (
            not fee.is_finite()
            or fee < 0
            or fee > Decimal('99999999.99')
            or fee.as_tuple().exponent < -2
        ):
            return JsonResponse(
                {'success': False, 'error': 'Each delivery fee must be between ₱0.00 and ₱99,999,999.99.'},
                status=400,
            )
        fee_rates[tier] = fee

    with transaction.atomic():
        station_availability, _ = StationAvailability.objects.get_or_create(pk=1)
        station_availability.delivery_fee_up_to_2km = fee_rates['up_to_2km']
        station_availability.delivery_fee_up_to_3km = fee_rates['up_to_3km']
        station_availability.save(update_fields=[
            *rate_fields.values(),
            'updated_at',
        ])

        orders_to_update = []
        updated_at = timezone.now()
        for order in Order.objects.exclude(status='delivered').iterator():
            delivery_fee, distance_km, delivery_area, requires_approval = calculate_delivery_fee(
                order.delivery_lat,
                order.delivery_lng,
                order.delivery_address,
                fee_rates,
            )
            previous_delivery_fee = order.delivery_fee
            order.delivery_fee = delivery_fee
            order.delivery_distance_km = distance_km
            order.delivery_area = delivery_area
            order.delivery_fee_requires_approval = requires_approval
            order.total_amount = order.total_amount - previous_delivery_fee + delivery_fee
            order.updated_at = updated_at
            orders_to_update.append(order)

        if orders_to_update:
            Order.objects.bulk_update(
                orders_to_update,
                [
                    'delivery_fee',
                    'delivery_distance_km',
                    'delivery_area',
                    'delivery_fee_requires_approval',
                    'total_amount',
                    'updated_at',
                ],
                batch_size=500,
            )

    return JsonResponse({
        'success': True,
        'fee_rates': {tier: str(fee) for tier, fee in fee_rates.items()},
        'updated_orders': len(orders_to_update),
    })


def get_order_json(request, order_id):















    from .models import OrderItem















    order = get_object_or_404(Order.objects.select_related('customer', 'rider').prefetch_related('items__product'), id=order_id)















    















    # Permission check: allow customer to view their own order, or staff/admin/rider















    user_role = request.user.profile.role if hasattr(request.user, 'profile') else None















    is_own_order = order.customer == request.user or order.rider == request.user















    is_staff_or_admin = user_role in ['staff', 'admin', 'rider']















    















    if not (is_own_order or is_staff_or_admin):















        return JsonResponse({'error': 'Unauthorized'}, status=403)















    















    # Build items list















    items = []















    if order.items.exists():















        for item in order.items.all():















            items.append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'product_price': str(item.unit_price),
                'product_image': item.product.get_main_image() or '/static/pos/images/default-product.png',
                'subtotal': str(item.subtotal)
            })















    















    data = {















        'order_number': order.order_number,















        'items': items,
        'subtotal': str(order.subtotal),
        'discount': str(order.discount),
        'delivery_fee': str(order.delivery_fee),
        'delivery_distance_km': str(order.delivery_distance_km),
        'delivery_area': order.delivery_area,
        'delivery_fee_requires_approval': order.delivery_fee_requires_approval,
        'total_amount': str(order.total_amount),















        'customer_name': order.customer.get_full_name() or order.customer.username,















        'customer_phone': order.customer.profile.phone_number,















        'delivery_address': order.delivery_address,















        'status': order.status,















        'status_display': (
            'On the Way'
            if order.status == 'out_for_delivery'
            else order.get_status_display()
        ),















        'rider_name': order.rider.get_full_name() or order.rider.username if order.rider else None,















        'rider_id': order.rider_id,















        'notes': order.notes,















        'payment_method_display': order.get_payment_method_display(),















        'created_at': order.created_at.isoformat(),















        'delivery_image': order.delivery_image.url if order.delivery_image else None,















        'delivered_at': order.delivered_at.strftime('%Y-%m-%d %H:%M') if order.delivered_at else None,















        'latitude': float(order.delivery_lat) if order.delivery_lat else None,















        'longitude': float(order.delivery_lng) if order.delivery_lng else None,















        'has_coordinates': order.has_coordinates,















    }















    return JsonResponse(data)















































# ===================== RIDER VIEWS =====================















@rider_required















def rider_accept_order(request, order_id):















    if request.method != 'POST':















        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)































    order = get_object_or_404(















        Order, id=order_id, rider=request.user,















        status__in=['pending', 'send-to-rider', 'out_for_delivery']















    )































    try:















        order.status = 'rider_accepted'















        order.save()















        return JsonResponse({'success': True})















    except Exception as e:















        return JsonResponse({'success': False, 'error': str(e)}, status=400)















































@rider_required















def rider_mark_out_for_delivery(request, order_id):















    if request.method != 'POST':















        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)















    















    order = get_object_or_404(







        Order, id=order_id, rider=request.user,







        status__in=['pending', 'processing', 'send-to-rider', 'rider_accepted']















    )















    















    try:















        order.status = 'out_for_delivery'















        order.save()















        return JsonResponse({
            'success': True,
            'status': order.status,
            'status_display': (
                'On the Way'
                if order.status == 'out_for_delivery'
                else order.get_status_display()
            ),
        })















    except Exception as e:















        return JsonResponse({'success': False, 'error': str(e)}, status=400)















































@rider_required















def rider_receive_order(request, order_id):















    if request.method != 'POST':















        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)















    















    order = get_object_or_404(















        Order, id=order_id, rider=request.user,















        status='out_for_delivery'















    )















    















    try:















        order.status = 'processing'















        order.save()















        return JsonResponse({'success': True})















    except Exception as e:















        return JsonResponse({'success': False, 'error': str(e)}, status=400)















































@rider_required















def rider_update_order_status(request, order_id):















    if request.method != 'POST':















        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)















    















    order = get_object_or_404(Order, id=order_id, rider=request.user)















    new_status = request.POST.get('status')















    















    if not new_status:















        return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)















    















    # Handle different status transitions















    if new_status == 'out_for_delivery':















        if order.status in ['pending', 'processing']:















            order.status = 'out_for_delivery'















            order.save()















            return JsonResponse({'success': True})















        else:















            return JsonResponse({'success': False, 'error': 'Cannot change status to Out for Delivery from current status'}, status=400)















    















    elif new_status == 'processing':















        if order.status == 'out_for_delivery':















            order.status = 'processing'















            order.save()















            return JsonResponse({'success': True})















        else:















            return JsonResponse({'success': False, 'error': 'Cannot receive order from current status'}, status=400)















    















    elif new_status == 'delivered':















        # For delivered, redirect to the modal form for image upload















        return JsonResponse({'success': False, 'error': 'Use Delivered button for marking as delivered'}, status=400)















    















    return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)















































@rider_required















def rider_mark_delivered(request, order_id=None):















    # Accept order_id from POST data as fallback















    if request.method == 'POST' and not order_id:















        order_id = request.POST.get('order_id')















    















    if not order_id:















        messages.error(request, 'Order ID is required.')















        return redirect('rider_dashboard')















    















    try:















        order = Order.objects.get(id=order_id, rider=request.user, status__in=['pending', 'processing', 'send-to-rider', 'out_for_delivery', 'rider_accepted'])















    except Order.DoesNotExist:















        messages.error(request, f'Order #{order_id} does not exist.')















        return redirect('rider_dashboard')















    















    if request.method == 'POST':















        old_status = order.status















        order.status = 'delivered'















        order.delivered_at = timezone.now()















        if 'delivery_image' in request.FILES:















            order.delivery_image = request.FILES['delivery_image']















        order.save()































        # If status changed to delivered, create a Sale in POS















        if old_status != 'delivered':















            from .models import OrderItem















            # Check if a sale already exists for this order















            existing_sale = Sale.objects.filter(order_number=order.order_number).first()
            if existing_sale and existing_sale.created_at < order.created_at:
                existing_sale.order_number = (
                    f'{order.order_number}-LEGACY-{existing_sale.pk}'
                )
                existing_sale.save(update_fields=['order_number'])
                existing_sale = None















            if not existing_sale:















                # Convert payment method















                payment_method = 'cash' if order.payment_method == 'cod' else order.payment_method































                # Create the sale















                sale = Sale.objects.create(















                    customer=order.customer,















                    cashier=order.rider or request.user,  # Use rider or current user as cashier















                    rider=order.rider,  # Set the rider















                    total_amount=order.total_amount,















                    payment_method=payment_method,















                    status='completed',















                    order_type='delivery',















                    order_number=order.order_number  # Link to original order















                )































                # Create sale items from order items















                for order_item in order.items.all():















                    SaleItem.objects.create(















                        sale=sale,
                        product=order_item.product,
                        order_item=order_item,
                        quantity=order_item.quantity,















                        unit_price=order_item.unit_price,















                        subtotal=order_item.subtotal















                    )































        messages.success(request, f'Order #{order.order_number} marked as delivered.')















        print(f"DEBUG: Order {order.order_number} status set to {order.status}")















    return redirect('rider_dashboard')















































# ===================== API endpoint for rider delivery locations =====================















@rider_required















def get_delivery_locations(request):















    orders = Order.objects.filter(















        rider=request.user,















        status__in=['pending', 'processing', 'out_for_delivery']















    ).select_related('customer', 'customer__profile')































    locations = []















    for order in orders:















        loc = {















            'id': order.id,















            'order_number': order.order_number,















            'customer_name': f"{order.customer.first_name} {order.customer.last_name}",















            'address': order.delivery_address,















            'phone': order.customer.profile.phone_number,















            'total_amount': float(order.total_amount),















            'notes': order.notes,















            'status': order.status,















        }















        if order.delivery_lat and order.delivery_lng:















            loc['latitude'] = float(order.delivery_lat)















            loc['longitude'] = float(order.delivery_lng)















        else:















            loc['latitude'] = None















            loc['longitude'] = None















        locations.append(loc)































    return JsonResponse({'locations': locations, 'count': len(locations)})















































# ===================== RIDER LOCATION UPDATE (for real-time tracking) =====================















@rider_required















@require_POST















def update_rider_location(request):















    try:















        data = json.loads(request.body)















        lat = float(data.get('lat'))















        lng = float(data.get('lng'))

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return JsonResponse({'ok': False, 'error': 'Invalid GPS coordinates.'}, status=400)















        profile = request.user.profile















        profile.default_latitude = lat















        profile.default_longitude = lng















        profile.save(update_fields=['default_latitude', 'default_longitude'])















        return JsonResponse({'ok': True})















    except Exception as e:















        return JsonResponse({'ok': False, 'error': str(e)}, status=400)















































# ===================== CUSTOMER: get rider live location =====================















@customer_required















def get_rider_location(request, order_id):















    order = get_object_or_404(Order, id=order_id, customer=request.user)















    if not order.rider:















        return JsonResponse({'has_rider': False, 'order_status': order.status})































    rider_profile = order.rider.profile















    if rider_profile.default_latitude and rider_profile.default_longitude:















        return JsonResponse({















            'has_rider': True,















            'rider_name': order.rider.get_full_name() or order.rider.username,















            'rider_phone': rider_profile.phone_number,















            'lat': float(rider_profile.default_latitude),















            'lng': float(rider_profile.default_longitude),















            'order_status': order.status,















            'order_status_display': order.get_status_display(),















        })















    else:















        return JsonResponse({















            'has_rider': True,















            'rider_name': order.rider.get_full_name() or order.rider.username,















            'rider_phone': rider_profile.phone_number,















            'lat': None,















            'lng': None,















            'order_status': order.status,















            'order_status_display': order.get_status_display(),















        })















































# ===================== MESSAGING / COMMUNICATION =====================















def _get_messaging_context(request):















    """Shared context for messaging pages across all roles."""















    user_role = request.user.profile.role















    if user_role == 'customer':















        contacts = User.objects.filter(















            profile__role__in=['admin', 'staff', 'rider'],















            is_active=True















        ).select_related('profile').order_by('profile__role', 'first_name')















        dashboard_url = 'customer_dashboard'















    elif user_role == 'rider':















        contacts = User.objects.filter(















            profile__role__in=['admin', 'staff', 'customer'],















            is_active=True















        ).select_related('profile').order_by('profile__role', 'first_name')















        dashboard_url = 'rider_dashboard'















    elif user_role in ['admin', 'staff']:















        contacts = User.objects.filter(















            profile__role__in=['admin', 'staff', 'rider', 'customer'],















            is_active=True















        ).exclude(id=request.user.id).select_related('profile').order_by('profile__role', 'first_name')















        dashboard_url = 'admin_dashboard' if user_role == 'admin' else 'staff_dashboard'















    else:















        contacts = User.objects.none()















        dashboard_url = 'customer_dashboard'































    conversations = Conversation.objects.filter(















        participants=request.user, is_active=True















    ).prefetch_related('participants', 'messages')































    total_unread = Message.objects.filter(















        conversation__participants=request.user,















        is_read=False















    ).exclude(sender=request.user).count()































    return {















        'contacts': contacts,















        'dashboard_url': dashboard_url,















        'conversations': conversations,















        'total_unread': total_unread,















        'user_role': user_role,















    }















































def messaging_inbox(request):















    """Inbox view — works for all authenticated roles."""















    if not request.user.is_authenticated:















        return redirect('login')































    ctx = _get_messaging_context(request)















    conversations = ctx['conversations']















    conv_list = []















    for conv in conversations:















        other = conv.get_other_participant(request.user)















        if not other:















            continue















        last_msg = conv.get_last_message()















        unread = conv.get_unread_count(request.user)















        conv_list.append({















            'conversation': conv,















            'other_user': other,















            'last_message': last_msg,















            'unread_count': unread,















        })































    ctx['conv_list'] = conv_list

    if request.GET.get('format') == 'json':
        return JsonResponse({
            'conversations': [
                {
                    'id': item['conversation'].id,
                    'preview': item['last_message'].content if item['last_message'] else '',
                    'unread_count': item['unread_count'],
                    'updated_at': item['conversation'].updated_at.isoformat(),
                }
                for item in conv_list
            ],
        })

    return render(request, 'accounts/messaging_inbox.html', ctx)















































def _message_order_payload(order):
    if not order:
        return None
    return {
        'order_number': order.order_number,
        'total_amount': f'{order.total_amount:.2f}',
        'payment_method': order.get_payment_method_display(),
        'items': [
            {
                'quantity': item.quantity,
                'product_name': item.product.name,
            }
            for item in order.items.all()
        ],
    }


def conversation_detail(request, conv_id):



    """View a single conversation and send a reply."""



    if not request.user.is_authenticated:



        return redirect('login')







    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)



    other_user = conversation.get_other_participant(request.user)







    # Mark messages as read



    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    if request.method == 'GET' and request.GET.get('format') == 'json':
        return JsonResponse({
            'messages': [
                {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'sender_name': message.sender.get_full_name() or message.sender.username,
                    'created_at': message.created_at.strftime('%I:%M %p · %b %d'),
                    'order': _message_order_payload(message.order),
                }
                for message in conversation.messages.select_related('sender', 'order').prefetch_related('order__items__product').all()
            ],
        })

    msg_list = conversation.messages.all()







    if request.method == 'POST':



        content = request.POST.get('content', '').strip()



        if content:



            message = Message.objects.create(



                conversation=conversation,



                sender=request.user,



                content=content



            )



            conversation.save(update_fields=['updated_at'])



            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('format') == 'json':
                return JsonResponse({'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'created_at': message.created_at.strftime('%I:%M %p · %b %d'),
                    'order': None,
                }})

            # If AJAX request, return updated conversation partial



            if request.GET.get('ajax') == '1':



                ctx = _get_messaging_context(request)



                ctx['conversation'] = conversation



                ctx['other_user'] = other_user



                ctx['messages'] = conversation.messages.all()



                return render(request, 'accounts/conversation_partial.html', ctx)



            return redirect('conversation_detail', conv_id=conversation.id)







    ctx = _get_messaging_context(request)



    ctx['conversation'] = conversation



    ctx['other_user'] = other_user



    ctx['messages'] = msg_list







    # Return partial template for AJAX requests



    if request.GET.get('ajax') == '1':



        return render(request, 'accounts/conversation_partial.html', ctx)







    return render(request, 'accounts/conversation_detail.html', ctx)















































def compose_message(request):















    """Start a new conversation with a selected user."""















    if not request.user.is_authenticated:















        return redirect('login')































    ctx = _get_messaging_context(request)































    if request.method == 'POST':















        recipient_id = request.POST.get('recipient')















        content = request.POST.get('content', '').strip()































        if recipient_id and content:















            recipient = get_object_or_404(User, id=recipient_id)































            # Check if conversation already exists between these two















            existing = Conversation.objects.filter(















                participants=request.user















            ).filter(















                participants=recipient















            ).filter(is_active=True).first()































            if existing:















                Message.objects.create(















                    conversation=existing,















                    sender=request.user,















                    content=content















                )















                existing.save(update_fields=['updated_at'])















                return redirect('conversation_detail', conv_id=existing.id)















            else:















                conv = Conversation.objects.create()















                conv.participants.add(request.user, recipient)















                Message.objects.create(















                    conversation=conv,















                    sender=request.user,















                    content=content















                )















                return redirect('conversation_detail', conv_id=conv.id)































    return render(request, 'accounts/compose_message.html', ctx)















































def start_conversation(request, user_id):

    """Start or redirect to an existing conversation with a specific user."""

    if not request.user.is_authenticated:

        return redirect('login')

    

    from django.shortcuts import get_object_or_404

    from .models import User, Conversation, Message

    

    recipient = get_object_or_404(User, id=user_id)

    

    # Check if conversation already exists between these two users

    existing = Conversation.objects.filter(

        participants=request.user

    ).filter(

        participants=recipient

    ).filter(is_active=True).first()

    

    if existing:

        # Redirect to existing conversation

        return redirect('conversation_detail', conv_id=existing.id)

    

    # Create new conversation

    conversation = Conversation.objects.create(is_active=True)

    conversation.participants.add(request.user, recipient)

    

    # Redirect to the new conversation

    return redirect('conversation_detail', conv_id=conversation.id)


@login_required
@require_POST
def rider_order_message(request, order_id):
    """Send a rider's delivery message to the customer assigned to an order."""
    order = get_object_or_404(Order, id=order_id, rider=request.user)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

    conversation = Conversation.objects.filter(
        participants=request.user,
        is_active=True,
    ).filter(
        participants=order.customer,
    ).first()
    if not conversation:
        conversation = Conversation.objects.create(is_active=True)
        conversation.participants.add(request.user, order.customer)

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        order=order,
        content=content,
    )
    conversation.save(update_fields=['updated_at'])
    return JsonResponse({
        'success': True,
        'message': message.content,
        'order': _message_order_payload(order),
        'conversation_url': reverse('conversation_detail', kwargs={'conv_id': conversation.id}),
    })


def unread_message_count_api(request):















    """API endpoint returning unread message count for the current user."""















    if not request.user.is_authenticated:















        return JsonResponse({'count': 0})































    count = Message.objects.filter(















        conversation__participants=request.user,















        is_read=False















    ).exclude(sender=request.user).count()















    return JsonResponse({'count': count})


@staff_required
def pending_order_count_api(request):
    """Return the number of customer orders that are not completed yet."""
    latest_order_id = Order.objects.order_by('-created_at', '-id').values_list(
        'id', flat=True
    ).first()
    latest_updated_at = Order.objects.order_by('-updated_at', '-id').values_list(
        'updated_at', flat=True
    ).first()
    return JsonResponse({
        'count': Order.objects.exclude(
            status__in=('delivered', 'cancelled')
        ).count(),
        'latest_order_id': latest_order_id,
        'latest_updated_at': (
            latest_updated_at.isoformat() if latest_updated_at else None
        ),
    })


@rider_required
def rider_order_updates_api(request):
    """Return a change token for the signed-in rider's active assignments."""
    active_statuses = (
        'pending',
        'processing',
        'send-to-rider',
        'out_for_delivery',
        'rider_accepted',
    )
    assigned_orders = Order.objects.filter(
        rider=request.user,
        status__in=active_statuses,
    )
    latest_order = assigned_orders.order_by('-updated_at', '-id').first()
    return JsonResponse({
        'count': assigned_orders.count(),
        'latest_updated_at': (
            latest_order.updated_at.isoformat() if latest_order else None
        ),
        'latest_order_id': latest_order.id if latest_order else None,
    })


@login_required
def live_updates_api(request):
    """Return shared live-data tokens for all authenticated role pages."""
    latest_order = Order.objects.order_by('-updated_at', '-id').first()
    latest_product = Product.objects.order_by('-updated_at', '-id').first()
    latest_sale = Sale.objects.order_by('-updated_at', '-id').first()
    latest_profile = UserProfile.objects.order_by('-updated_at', '-id').first()
    latest_task = MaintenanceTask.objects.order_by('-updated_at', '-id').first()
    latest_report = MaintenanceReport.objects.order_by('-updated_at', '-id').first()
    station_availability, _ = StationAvailability.objects.get_or_create(pk=1)
    unread_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()
    notification_unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        is_archived=False,
    ).count()
    low_stock_count = Product.objects.filter(
        is_active=True,
        stock_quantity__lte=F('reorder_level'),
    ).count()

    data = {
        'user_role': request.user.profile.role,
        'station_is_open': station_availability.is_open,
        'delivery_fee_rates': {
            'up_to_2km': str(station_availability.delivery_fee_up_to_2km),
            'up_to_3km': str(station_availability.delivery_fee_up_to_3km),
        },
        'unread_count': unread_count,
        'notification_unread_count': notification_unread_count,
        'low_stock_count': low_stock_count,
        'orders': {
            'latest_updated_at': (
                latest_order.updated_at.isoformat() if latest_order else None
            ),
            'latest_id': latest_order.id if latest_order else None,
        },
        'products': {
            'latest_updated_at': (
                latest_product.updated_at.isoformat() if latest_product else None
            ),
            'latest_id': latest_product.id if latest_product else None,
        },
        'sales': {
            'latest_updated_at': (
                latest_sale.updated_at.isoformat() if latest_sale else None
            ),
            'latest_id': latest_sale.id if latest_sale else None,
        },
        'users': {
            'latest_updated_at': (
                latest_profile.updated_at.isoformat() if latest_profile else None
            ),
            'latest_id': latest_profile.id if latest_profile else None,
        },
        'maintenance': {
            'latest_task_updated_at': (
                latest_task.updated_at.isoformat() if latest_task else None
            ),
            'latest_task_id': latest_task.id if latest_task else None,
            'latest_report_updated_at': (
                latest_report.updated_at.isoformat() if latest_report else None
            ),
            'latest_report_id': latest_report.id if latest_report else None,
        },
    }
    if request.user.profile.role in ('admin', 'staff'):
        latest_return_request = ReturnRequest.objects.order_by(
            '-updated_at', '-id'
        ).values('id', 'updated_at', 'pickup_status').first()
        data['return_requests'] = {
            'latest_updated_at': (
                latest_return_request['updated_at'].isoformat()
                if latest_return_request else None
            ),
            'latest_id': latest_return_request['id'] if latest_return_request else None,
            'latest_pickup_status': (
                latest_return_request['pickup_status']
                if latest_return_request else None
            ),
        }
        data['pending_orders'] = Order.objects.exclude(
            status__in=('delivered', 'cancelled')
        ).count()
        data['order_notification_count'] = data['pending_orders']
        latest_customer_order = latest_order
        data['latest_customer_order'] = (
            {
                'id': latest_customer_order.id,
                'order_number': latest_customer_order.order_number,
                'created_at': latest_customer_order.created_at.isoformat(),
                'status': latest_customer_order.status,
                'status_display': (
                    'On the Way'
                    if latest_customer_order.status == 'out_for_delivery'
                    else latest_customer_order.get_status_display()
                ),
            }
            if latest_customer_order else None
        )
    elif request.user.profile.role == 'rider':
        data['assigned_orders'] = Order.objects.filter(
            rider=request.user,
            status__in=(
                'pending',
                'processing',
                'send-to-rider',
                'out_for_delivery',
                'rider_accepted',
            ),
        ).count()
        rider_return_pickups = ReturnRequest.objects.filter(
            pickup_rider=request.user,
            status='approved',
            pickup_status__in=('assigned', 'picked_up', 'payment_returned'),
        )
        latest_return_pickup = rider_return_pickups.order_by(
            '-updated_at', '-id'
        ).values('id', 'updated_at', 'pickup_status').first()
        data['return_pickups'] = {
            'count': rider_return_pickups.count(),
            'latest_updated_at': (
                latest_return_pickup['updated_at'].isoformat()
                if latest_return_pickup else None
            ),
            'latest_id': latest_return_pickup['id'] if latest_return_pickup else None,
            'latest_pickup_status': (
                latest_return_pickup['pickup_status']
                if latest_return_pickup else None
            ),
        }
        data['order_notification_count'] = data['assigned_orders']
    else:
        customer_return_requests = ReturnRequest.objects.filter(
            order__customer=request.user
        )
        latest_customer_return = customer_return_requests.order_by(
            '-updated_at', '-id'
        ).values('id', 'updated_at', 'pickup_status').first()
        data['customer_returns'] = {
            'count': customer_return_requests.count(),
            'latest_updated_at': (
                latest_customer_return['updated_at'].isoformat()
                if latest_customer_return else None
            ),
            'latest_id': latest_customer_return['id'] if latest_customer_return else None,
            'latest_pickup_status': (
                latest_customer_return['pickup_status']
                if latest_customer_return else None
            ),
        }
        customer_orders = Order.objects.filter(customer=request.user).exclude(
            status__in=('delivered', 'cancelled')
        )
        data['customer_orders'] = customer_orders.count()
        data['order_notification_count'] = data['customer_orders']
        data['customer_order_updates'] = [
            {
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'status_display': (
                    'On the Way'
                    if order.status == 'out_for_delivery'
                    else order.get_status_display()
                ),
                'updated_at': order.updated_at.isoformat(),
            }
            for order in Order.objects.filter(customer=request.user).order_by(
                '-updated_at', '-id'
            )[:20]
        ]
    return JsonResponse(data)


@login_required
def station_availability_api(request):
    availability, _ = StationAvailability.objects.get_or_create(pk=1)
    if request.method == 'POST':
        if not request.user.profile.role in ('admin', 'staff'):
            return JsonResponse({'error': 'You are not allowed to change station availability.'}, status=403)
        try:
            is_open = request.POST.get('is_open', '').lower() == 'true'
        except AttributeError:
            return JsonResponse({'error': 'Invalid station availability.'}, status=400)
        availability.is_open = is_open
        availability.save(update_fields=['is_open', 'updated_at'])
    return JsonResponse({'is_open': availability.is_open})


@login_required
@admin_required
def wifi_configuration(request):
    configuration = WifiConfiguration.objects.order_by('-updated_at').first()
    if request.method == 'POST':
        ssid = request.POST.get('ssid', '').strip()
        password = request.POST.get('password', '')
        if not ssid:
            messages.error(request, 'Wi-Fi SSID is required.')
        elif not password and configuration is None:
            messages.error(request, 'Wi-Fi password is required.')
        else:
            if configuration is None:
                configuration = WifiConfiguration()
            configuration.ssid = ssid
            if password:
                configuration.password = password
            configuration.save()
            messages.success(request, 'Wi-Fi credentials saved successfully.')
            return redirect('wifi_configuration')
    wifi_device_endpoint = ''
    wifi_device_endpoint_warning = ''
    if configuration:
        endpoint_path = reverse(
            'wifi_device_credentials',
            args=[configuration.device_token],
        )
        base_url = getattr(settings, 'WIFI_CREDENTIALS_BASE_URL', '')
        wifi_device_endpoint = (
            f'{base_url}{endpoint_path}'
            if base_url else request.build_absolute_uri(endpoint_path)
        )
        endpoint_host = urlsplit(wifi_device_endpoint).hostname
        if endpoint_host in {'localhost', '127.0.0.1', '::1', '0.0.0.0'}:
            wifi_device_endpoint_warning = (
                'This endpoint uses localhost and cannot be reached by the ESP12E. '
                'Set WIFI_CREDENTIALS_BASE_URL to the server LAN/public URL, or open '
                'this page using the server computer LAN IP. For local testing, run '
                'Django on 0.0.0.0:8000.'
            )
        elif wifi_device_endpoint.startswith('http://'):
            wifi_device_endpoint_warning = (
                'This HTTP endpoint is suitable only for testing on a trusted local '
                'network. Use HTTPS for deployment.'
            )

    return render(request, 'accounts/wifi_configuration.html', {
        'wifi_configuration': configuration,
        'wifi_device_endpoint': wifi_device_endpoint,
        'wifi_device_endpoint_warning': wifi_device_endpoint_warning,
    })


@require_http_methods(["GET"])
def wifi_device_credentials(request, device_token):
    configuration = get_object_or_404(WifiConfiguration, device_token=device_token)
    response = JsonResponse({
        'ssid': configuration.ssid,
        'password': configuration.password,
        'updated_at': configuration.updated_at.isoformat(),
    })
    response['Cache-Control'] = 'no-store'
    return response


@login_required
def notifications_api(request):
    role = request.user.profile.role
    notification_filters = {'recipient': request.user, 'is_archived': False}
    if role == 'customer':
        notification_filters['category__in'] = ('orders', 'announcement')
    elif role == 'rider':
        notification_filters['category__in'] = ('orders', 'messages')
    elif role == 'staff':
        notification_filters['category__in'] = ('orders', 'messages', 'inventory', 'maintenance')
    notifications = Notification.objects.filter(
        **notification_filters,
    )[:100]
    payload = [
        {
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'category': item.category,
            'category_label': item.get_category_display(),
            'severity': item.severity,
            'target_url': item.target_url,
            'is_read': item.is_read,
            'created_at': item.created_at.isoformat(),
        }
        for item in notifications
    ]

    if role != 'customer':
        unread_message_count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()
        if unread_message_count:
            payload.insert(0, {
                'id': 'unread-messages',
                'title': 'Unread messages',
                'description': f'You have {unread_message_count} unread message(s).',
                'category': 'messages',
                'category_label': 'Messages',
                'severity': 'info',
                'target_url': reverse('messaging_inbox'),
                'is_read': False,
                'created_at': timezone.now().isoformat(),
            })

    if role in ('admin', 'staff'):
        unread_contact_messages = (
            ContactMessage.objects.filter(
                recipient_id=request.user.pk,
                is_read=False,
            ).order_by('-created_at')
            if isinstance(request.user, User)
            else []
        )
        latest_contact_message = (
            unread_contact_messages.first()
            if hasattr(unread_contact_messages, 'first')
            else None
        )
        if latest_contact_message:
            unread_contact_count = unread_contact_messages.count()
            payload.insert(0, {
                'id': f'contact-message-{latest_contact_message.id}',
                'title': 'New customer inquiry',
                'description': (
                    f'{latest_contact_message.name} sent a message through the contact form.'
                    if unread_contact_count == 1
                    else f'You have {unread_contact_count} new messages through the contact form.'
                ),
                'category': 'messages',
                'category_label': 'Customer messages',
                'severity': 'info',
                'target_url': reverse('contact_messages'),
                'is_read': False,
                'created_at': latest_contact_message.created_at.isoformat(),
            })
        low_stock_count = Product.objects.filter(
            is_active=True,
            stock_quantity__lte=F('reorder_level'),
        ).count()
        if low_stock_count:
            payload.insert(0, {
                'id': 'low-stock',
                'title': 'Low stock alert',
                'description': f'{low_stock_count} product(s) are at or below reorder level.',
                'category': 'inventory',
                'category_label': 'Inventory',
                'severity': 'warning',
                'target_url': reverse('inventory_list') + '?low_stock=1',
                'is_read': True,
                'created_at': timezone.now().isoformat(),
            })

        active_order_count = Order.objects.exclude(
            status__in=('delivered', 'cancelled')
        ).count()
        if active_order_count:
            payload.insert(0, {
                'id': 'active-orders',
                'title': 'Orders need attention',
                'description': f'{active_order_count} active order(s) are awaiting completion.',
                'category': 'orders',
                'category_label': 'Orders',
                'severity': 'info',
                'target_url': reverse('manage_orders'),
                'is_read': True,
                'created_at': timezone.now().isoformat(),
            })
    elif role == 'rider':
        assigned_order_count = Order.objects.filter(
            rider=request.user,
            status__in=(
                'pending',
                'processing',
                'send-to-rider',
                'out_for_delivery',
                'rider_accepted',
            ),
        ).count()
        if assigned_order_count:
            payload.insert(0, {
                'id': 'assigned-orders',
                'title': 'Assigned deliveries',
                'description': f'You have {assigned_order_count} active delivery assignment(s).',
                'category': 'orders',
                'category_label': 'Orders',
                'severity': 'info',
                'target_url': reverse('rider_dashboard'),
                'is_read': True,
                'created_at': timezone.now().isoformat(),
            })
    else:
        saved_announcement_urls = {
            item['target_url']
            for item in payload
            if item['category'] == 'announcement'
        }
        for announcement in AdminAnnouncementImage.objects.all():
            announcement_url = (
                reverse('customer_dashboard')
                + f'#customer-announcement-{announcement.id}'
            )
            if announcement_url in saved_announcement_urls:
                continue
            payload.append({
                'id': f'announcement-{announcement.id}',
                'title': announcement.headline or announcement.get_category_display(),
                'description': (
                    announcement.description
                    or 'A station announcement is available.'
                ),
                'category': 'announcement',
                'category_label': 'Announcement',
                'severity': 'info',
                'target_url': announcement_url,
                'is_read': True,
                'created_at': announcement.created_at.isoformat(),
            })
        active_customer_orders = Order.objects.filter(
            customer=request.user,
        ).exclude(status__in=('delivered', 'cancelled')).count()
        if active_customer_orders:
            payload.insert(0, {
                'id': 'customer-orders',
                'title': 'Active orders',
                'description': f'You have {active_customer_orders} active order(s).',
                'category': 'orders',
                'category_label': 'Orders',
                'severity': 'info',
                'target_url': reverse('customer_orders'),
                'is_read': True,
                'created_at': timezone.now().isoformat(),
            })
    return JsonResponse({
        'notifications': payload,
        'unread_count': sum(not item['is_read'] for item in payload),
        'read_all_at': (
            getattr(request.user.profile, 'notifications_read_at', None).isoformat()
            if getattr(request.user.profile, 'notifications_read_at', None)
            else None
        ),
    })


@login_required
@require_POST
def notification_action_api(request, notification_id=None):
    if notification_id:
        item = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
            is_archived=False,
        )
        action = json.loads(request.body or '{}').get('action', 'read')
        if action == 'archive':
            item.is_archived = True
        else:
            item.is_read = True
        item.save(update_fields=['is_read', 'is_archived'])
    else:
        action = json.loads(request.body or '{}').get('action', 'read')
        queryset = Notification.objects.filter(
            recipient=request.user,
            is_archived=False,
        )
        if action == 'archive':
            queryset.update(is_archived=True)
        else:
            queryset.update(is_read=True)
            Message.objects.filter(
                conversation__participants=request.user,
                is_read=False,
            ).exclude(sender=request.user).update(is_read=True)
            if isinstance(request.user, User):
                ContactMessage.objects.filter(
                    recipient_id=request.user.pk,
                    is_read=False,
                ).update(is_read=True)
            profile = getattr(request.user, 'profile', None)
            if profile is not None and hasattr(profile, 'notifications_read_at'):
                profile.notifications_read_at = timezone.now()
                profile.save(update_fields=['notifications_read_at'])
    return JsonResponse({'ok': True})


@login_required
def notifications_page(request):
    return render(request, 'accounts/notifications.html')


@login_required
@admin_required
def contact_messages_page(request):
    contact_messages = ContactMessage.objects.filter(
        recipient=request.user,
    ).order_by('-created_at')
    unread_messages = contact_messages.filter(is_read=False)
    unread_messages.update(is_read=True)
    return render(request, 'accounts/contact_messages.html', {
        'contact_messages': contact_messages,
    })














































# ===================== LANDING PAGE / HOME =====================















def home(request):

    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    return render(request, 'accounts/home.html')


@require_POST
def submit_contact_message(request):
    """Save a visitor's contact message for an administrator to process."""
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    content = request.POST.get('message', '').strip()

    if not name or not email or not content:
        return JsonResponse(
            {'success': False, 'message': 'Please complete all required fields.'},
            status=400,
        )

    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {'success': False, 'message': 'Please enter a valid email address.'},
            status=400,
        )

    admin_user = User.objects.filter(
        is_active=True,
        profile__role='admin',
    ).order_by('id').first()
    if admin_user is None:
        admin_user = User.objects.filter(is_superuser=True, is_active=True).order_by('id').first()

    if admin_user is None:
        logger.error('Contact form submission failed: no active administrator account exists.')
        return JsonResponse(
            {'success': False, 'message': 'Messages are temporarily unavailable. Please try again later.'},
            status=503,
        )

    ContactMessage.objects.create(
        recipient=admin_user,
        name=name,
        email=email,
        phone=phone,
        content=content,
    )
    return JsonResponse({'success': True, 'message': 'Message sent successfully! We will get back to you soon.'})


def legal_policy(request, policy_type):
    if policy_type not in {'terms', 'privacy'}:
        raise Http404("Policy page not found.")

    template_name = (
        'accounts/terms_of_service.html'
        if policy_type == 'terms'
        else 'accounts/privacy_policy.html'
    )
    return render(request, template_name)















































# ===================== POS VIEWS =====================















from decimal import Decimal































@staff_required















def pos_dashboard(request):















    """Main POS dashboard"""















    products = Product.objects.filter(is_active=True).order_by('name')















    customers = User.objects.filter(profile__role='customer', is_active=True)































    # Today's sales















    today = timezone.now().date()















    today_sales = Sale.objects.filter(created_at__date=today, status='completed')















    today_revenue = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0















    today_transactions = today_sales.count()















    today_customers = today_sales.values('customer').distinct().count()































    # Product statistics















    total_products = Product.objects.filter(is_active=True).count()















    low_stock_products = Product.objects.filter(















        is_active=True,















        stock_quantity__lte=F('reorder_level')















    )[:10]















    low_stock_count = low_stock_products.count()































    # Recent sales















    recent_sales = Sale.objects.select_related('customer', 'cashier').prefetch_related('items').order_by('-created_at')[:10]































    context = {















        'products': products,















        'customers': customers,















        'today_revenue': today_revenue,















        'today_transactions': today_transactions,















        'today_customers': today_customers,















        'total_products': total_products,















        'low_stock_products': low_stock_products,















        'low_stock_count': low_stock_count,















        'recent_sales': recent_sales,















    }















    return render(request, 'accounts/pos_dashboard.html', context)































@staff_required















def create_sale(request):















    """Create a new sale (POS transaction)"""





    if request.method == 'POST':
        sale_data = request.POST.copy()
        if sale_data.get('customer') == 'walkin':
            sale_data['customer'] = ''
        sale_form = SaleForm(sale_data)















        cart_data = request.POST.get('cart_data', '[]')















        amount_paid = request.POST.get('amount_paid', '0')































        try:















            cart = json.loads(cart_data)















        except:















            cart = []































        if sale_form.is_valid() and cart:















            with transaction.atomic():















                # Calculate totals















                subtotal = Decimal('0')















                for item in cart:















                    product = Product.objects.get(id=item['product_id'])















                    subtotal += Decimal(item['quantity']) * product.price































                # Get discount from POST (promo applied on frontend)















                try:















                    discount = Decimal(request.POST.get('discount', '0') or '0')















                except:















                    discount = Decimal('0')































                total = max(Decimal('0'), subtotal - discount)































                try:















                    amount_paid_decimal = Decimal(amount_paid) if amount_paid else Decimal('0')















                except:
                    amount_paid_decimal = Decimal('0')

















                if amount_paid_decimal <= 0 or amount_paid_decimal < total:
                    messages.error(
                        request,
                        f'Insufficient payment. Paid ₱{amount_paid_decimal:.2f} but total is ₱{total:.2f}.',
                    )
                    return redirect('create_sale')
















                change = amount_paid_decimal - total if amount_paid_decimal > total else Decimal('0')































                # Create sale















                sale = sale_form.save(commit=False)















                sale.cashier = request.user















                sale.subtotal = subtotal















                sale.discount = discount















                sale.total_amount = total















                sale.amount_paid = amount_paid_decimal















                sale.change_amount = change































                # Assign rider if provided (delivery orders)















                rider_id = request.POST.get('rider', '')















                if rider_id:















                    try:















                        sale.rider = User.objects.get(id=rider_id, profile__role='rider')















                    except User.DoesNotExist:















                        pass































                # Set order type















                order_type = request.POST.get('order_type', 'walkin')















                if hasattr(sale, 'order_type'):















                    sale.order_type = order_type































                # Set customer from hidden field if provided















                customer_id = request.POST.get('customer', '')















                if customer_id and customer_id != 'walkin':















                    try:















                        sale.customer = User.objects.get(id=customer_id, profile__role='customer')















                    except User.DoesNotExist:















                        sale.customer = None















                else:















                    sale.customer = None































                sale.save()































                # Create sale items and update inventory















                for item in cart:















                    product = Product.objects.get(id=item['product_id'])















                    quantity = int(item['quantity'])































                    SaleItem.objects.create(















                        sale=sale,















                        product=product,















                        quantity=quantity,















                        unit_price=product.price,















                        subtotal=quantity * product.price















                    )































                    old_stock = product.stock_quantity















                    product.stock_quantity -= quantity















                    product.save()































                    InventoryTransaction.objects.create(















                        product=product,















                        transaction_type='sale',















                        quantity=-quantity,















                        previous_stock=old_stock,















                        new_stock=product.stock_quantity,















                        reference=f"Sale #{sale.receipt_number}",















                        created_by=request.user















                    )































                    if sale.customer:















                        consumer, _ = Consumer.objects.get_or_create(user=sale.customer)















                        consumer.total_orders += 1















                        consumer.last_order_date = timezone.now()















                        consumer.save()































                messages.success(request, f'Sale completed! Receipt: {sale.receipt_number}')































                # Staff goes back to their dashboard, admin/others go to sale detail















                if hasattr(request.user, 'profile') and request.user.profile.role == 'staff':















                    return redirect('staff_dashboard')















                return redirect('sale_detail', sale_id=sale.id)















        else:















            messages.error(request, 'Please add items to cart and fill all required fields.')































    sale_form = SaleForm()















    products = Product.objects.filter(is_active=True).filter(
        Q(product_type='refill') | Q(stock_quantity__gt=0)
    ).order_by('name')
    refill_products = products.filter(product_type='refill')
    gallon_products = products.filter(product_type='gallon')















    categories = Category.objects.all()















    customers = User.objects.filter(profile__role='customer', is_active=True)















    riders = User.objects.filter(profile__role='rider', is_active=True).order_by('first_name')































    context = {















        'sale_form': sale_form,















        'products': products,
        'refill_products': refill_products,
        'gallon_products': gallon_products,
        'refill_product_count': refill_products.count(),
        'gallon_product_count': gallon_products.count(),















        'categories': categories,















        'customers': customers,















        'riders': riders,















    }















    return render(request, 'accounts/create_sale.html', context)































@staff_required















def sale_detail(request, sale_id):















    """View sale details"""















    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'cashier')
        .prefetch_related('items__product__images'),
        id=sale_id,
    )















    return render(request, 'accounts/sale_detail.html', {'sale': sale})































@staff_required















def sale_list(request):















    """List all sales"""















    sales = Sale.objects.select_related('customer', 'cashier').prefetch_related(
        'items__product'
    ).order_by('-created_at')































    # Filter by date















    date_from = request.GET.get('date_from', '')















    date_to = request.GET.get('date_to', '')































    if date_from and date_to:















        sales = sales.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)















    elif date_from:















        sales = sales.filter(created_at__date__gte=date_from)















    elif date_to:















        sales = sales.filter(created_at__date__lte=date_to)































    # Filter by status















    status = request.GET.get('status', '')















    if status:















        sales = sales.filter(status=status)































    # Search















    search = request.GET.get('search', '')















    if search:















        sales = sales.filter(















            Q(receipt_number__icontains=search) |















            Q(customer__username__icontains=search) |















            Q(customer__first_name__icontains=search)















        )































    context = {















        'sales': sales,















        'date_from': date_from,















        'date_to': date_to,















        'status': status,















        'search': search,















    }















    return render(request, 'accounts/sale_list.html', context)































@staff_required















def product_list(request):















    """Manage products"""















    products = Product.objects.select_related('category').all().order_by('name')































    # Filter by category















    category_id = request.GET.get('category', '')















    if category_id:















        products = products.filter(category_id=category_id)































    # Filter by active status















    active = request.GET.get('active', '')















    if active == '1':















        products = products.filter(is_active=True)















    elif active == '0':















        products = products.filter(is_active=False)































    categories = Category.objects.all()































    context = {















        'products': products,















        'categories': categories,















        'selected_category': int(category_id) if category_id else None,















        'active_filter': active,















    }















    return render(request, 'accounts/product_list.html', context)































@staff_required















def product_create(request):















    """Create a new product"""















    categories = Category.objects.all()































    if request.method == 'POST':















        form = ProductForm(request.POST, request.FILES)















        if form.is_valid():















            product = form.save()
            if form.cleaned_data.get('image'):
                ProductImage.objects.create(
                    product=product,
                    image=form.cleaned_data['image'],
                    is_main=True,
                )































            # Create initial inventory transaction















            if product.stock_quantity > 0:















                InventoryTransaction.objects.create(















                    product=product,















                    transaction_type='purchase',















                    quantity=product.stock_quantity,















                    previous_stock=0,















                    new_stock=product.stock_quantity,















                    reference="Initial stock",















                    created_by=request.user















                )































            messages.success(request, f'Product "{product.name}" created successfully!')















            return redirect('inventory_list')















    else:















        form = ProductForm()































    return render(request, 'accounts/product_form.html', {















        'form': form,















        'title': 'Add Product',















        'categories': categories,















    })































@staff_required

@require_http_methods(["POST"])

def product_delete(request, product_id):
    """Delete a product"""

    product = get_object_or_404(Product, id=product_id)
    product_name = product.name

    try:
        product.delete()
    except ProtectedError:
        product.is_active = False
        product.save(update_fields=['is_active', 'updated_at'])
        messages.success(
            request,
            f'Product "{product_name}" was archived because it has existing sales or orders.'
        )
    else:
        messages.success(request, f'Product "{product_name}" deleted successfully!')

    return redirect('inventory_list')



@staff_required















def product_edit(request, product_id):















    """Edit a product"""

    product = get_object_or_404(Product, id=product_id)
    requested_product_type = request.GET.get('product_type')
    edit_product_type = (
        requested_product_type
        if requested_product_type in {'refill', 'gallon'}
        else product.product_type
    )

    categories = Category.objects.all()

    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['product_type'] = edit_product_type
        form = ProductForm(post_data, request.FILES, instance=product)















        if form.is_valid():















            form.save()
            if form.cleaned_data.get('image'):
                product.images.update(is_main=False)
                ProductImage.objects.create(
                    product=product,
                    image=form.cleaned_data['image'],
                    is_main=True,
                )















            messages.success(request, f'Product "{product.name}" updated successfully!')















            return redirect('inventory_list')















    else:















        form = ProductForm(instance=product)































    return render(request, 'accounts/product_form.html', {















        'form': form,















        'title': 'Edit Product',
        'product': product,
        'edit_product_type': edit_product_type,
        'categories': categories,















    })































@staff_required















def inventory_list(request):















    """View inventory and stock levels"""















    products = Product.objects.filter(
        is_active=True,
        product_type='gallon',
    ).select_related('category').order_by('name')
    refill_products = Product.objects.filter(
        is_active=True,
        product_type='refill',
    ).select_related('category').order_by('name')































    # Filter low stock















    low_stock_only = request.GET.get('low_stock', '')















    if low_stock_only:















        products = products.filter(stock_quantity__lte=F('reorder_level'))































    # Show only sold Water Gallon products in the inventory history.
    recent_transactions = InventoryTransaction.objects.filter(
        product__product_type='gallon',
        transaction_type='sale',
    ).select_related('product', 'created_by').order_by('-created_at')[:50]































    context = {















        'products': products,
        'refill_products': refill_products,















        'recent_transactions': recent_transactions,















        'low_stock_only': low_stock_only,















    }















    return render(request, 'accounts/inventory_list.html', context)































def _report_period_default_start(period, end_date):
    if period == 'weekly':
        return end_date - timedelta(days=end_date.weekday())
    if period == 'monthly':
        return end_date.replace(day=1)
    return end_date


@staff_required
def sales_report(request):















    """Generate sales reports"""















    # Get period parameter (daily, weekly, monthly)

    period = request.GET.get('period', 'daily').lower()
    if period not in ('daily', 'weekly', 'monthly'):
        period = 'daily'









    end_date = timezone.localdate()
    default_start = _report_period_default_start(period, end_date)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')































    try:
        start = (
            datetime.strptime(date_from, '%Y-%m-%d').date()
            if date_from else default_start
        )
        end = (
            datetime.strptime(date_to, '%Y-%m-%d').date()
            if date_to else end_date
        )
    except ValueError:
        start = default_start
        end = end_date

    if end < start:
        start, end = end, start































    # Get sales in date range with optimized queries















    sales = Sale.objects.filter(















        created_at__date__gte=start,















        created_at__date__lte=end,















        status='completed'















    ).annotate(
        net_revenue=F('total_amount') - F('returned_amount'),
    ).select_related('customer', 'cashier').prefetch_related('items__product').order_by('-created_at')































    # Summary statistics









    total_sales = sales.count()















    total_revenue = sales.aggregate(Sum('net_revenue'))['net_revenue__sum'] or 0
    delivery_order_numbers = [number for number in sales.values_list('order_number', flat=True) if number]
    delivery_fee_total = Order.objects.filter(
        order_number__in=delivery_order_numbers
    ).aggregate(Sum('delivery_fee'))['delivery_fee__sum'] or 0















    average_sale = total_revenue / total_sales if total_sales > 0 else 0































    # Calculate total items sold (sum of all quantities)















    total_items_sold = SaleItem.objects.filter(
        sale__in=sales
    ).aggregate(total=Sum(F('quantity') - F('returned_quantity')))['total'] or 0































    # Sales by payment method (original - for reference)















    payment_methods = sales.values('payment_method').annotate(















        count=Count('id'),















        total=Sum('net_revenue')















    )































    # Calculate aggregated totals for Cash and GCash only















    cash_total = 0















    gcash_total = 0















    cash_count = 0















    gcash_count = 0































    for sale in sales:















        if sale.payment_method == 'cash':















            cash_total += sale.net_amount















            cash_count += 1















        elif sale.payment_method == 'gcash':















            gcash_total += sale.net_amount















            gcash_count += 1





















    # Create sales data based on period (daily, weekly, monthly)

    sales_data = []

    

    if period == 'daily':

        # Group sales by date

        sales_by_date = {}

        for sale in sales:

            sale_date = sale.created_at.date()

            if sale_date not in sales_by_date:

                sales_by_date[sale_date] = {'cash': 0, 'gcash': 0}

            if sale.payment_method == 'cash':

                sales_by_date[sale_date]['cash'] += sale.net_amount

            elif sale.payment_method == 'gcash':

                sales_by_date[sale_date]['gcash'] += sale.net_amount

        

        current_date = start

        while current_date <= end:

            day_data = sales_by_date.get(current_date, {'cash': 0, 'gcash': 0})

            day_label = current_date.strftime('%a %d')

            sales_data.append({

                'label': day_label,

                'day_number': current_date.day,

                'day_name': current_date.strftime('%A'),

                'full_date': current_date.strftime('%Y-%m-%d'),

                'month_year': current_date.strftime('%B %Y'),

                'cash_total': float(day_data['cash']),

                'gcash_total': float(day_data['gcash']),

                'total': float(day_data['cash'] + day_data['gcash'])

            })

            current_date += timedelta(days=1)

    

    elif period == 'weekly':

        # Group sales by week

        sales_by_week = {}

        for sale in sales:

            sale_date = sale.created_at.date()

            # Get the start of the week (Monday)

            week_start = sale_date - timedelta(days=sale_date.weekday())

            week_key = week_start.strftime('%Y-%W')

            if week_key not in sales_by_week:

                sales_by_week[week_key] = {'cash': 0, 'gcash': 0, 'week_start': week_start}

            if sale.payment_method == 'cash':

                sales_by_week[week_key]['cash'] += sale.net_amount

            elif sale.payment_method == 'gcash':

                sales_by_week[week_key]['gcash'] += sale.net_amount

        

        # Sort weeks and create data

        sorted_weeks = sorted(sales_by_week.keys())

        for week_key in sorted_weeks:

            week_data = sales_by_week[week_key]

            week_start = week_data['week_start']

            week_end = week_start + timedelta(days=6)

            week_label = f"Week {week_start.strftime('%W')}"

            sales_data.append({

                'label': week_label,

                'day_name': f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}",

                'full_date': week_start.strftime('%Y-%m-%d'),

                'month_year': week_start.strftime('%B %Y'),

                'cash_total': float(week_data['cash']),

                'gcash_total': float(week_data['gcash']),

                'total': float(week_data['cash'] + week_data['gcash'])

            })

    

    elif period == 'monthly':

        # Group sales by month

        sales_by_month = {}

        for sale in sales:

            sale_date = sale.created_at.date()

            month_key = sale_date.strftime('%Y-%m')

            if month_key not in sales_by_month:

                sales_by_month[month_key] = {'cash': 0, 'gcash': 0, 'month_date': sale_date}

            if sale.payment_method == 'cash':

                sales_by_month[month_key]['cash'] += sale.net_amount

            elif sale.payment_method == 'gcash':

                sales_by_month[month_key]['gcash'] += sale.net_amount

        

        # Sort months and create data

        sorted_months = sorted(sales_by_month.keys())

        for month_key in sorted_months:

            month_data = sales_by_month[month_key]

            month_date = month_data['month_date']

            month_label = month_date.strftime('%b %Y')

            sales_data.append({

                'label': month_label,

                'day_name': month_date.strftime('%B %Y'),

                'full_date': month_date.strftime('%Y-%m-%d'),

                'month_year': month_date.strftime('%B %Y'),

                'cash_total': float(month_data['cash']),

                'gcash_total': float(month_data['gcash']),

                'total': float(month_data['cash'] + month_data['gcash'])

            })

    

    # Default to daily if no valid period

    if not sales_data and period == 'daily':

        period = 'daily'

        sales_by_date = {}

        for sale in sales:

            sale_date = sale.created_at.date()

            if sale_date not in sales_by_date:

                sales_by_date[sale_date] = {'cash': 0, 'gcash': 0}

            if sale.payment_method == 'cash':

                sales_by_date[sale_date]['cash'] += sale.net_amount

            elif sale.payment_method == 'gcash':

                sales_by_date[sale_date]['gcash'] += sale.net_amount

        

        current_date = start

        while current_date <= end:

            day_data = sales_by_date.get(current_date, {'cash': 0, 'gcash': 0})

            day_label = current_date.strftime('%a %d')

            sales_data.append({

                'label': day_label,

                'day_number': current_date.day,

                'day_name': current_date.strftime('%A'),

                'full_date': current_date.strftime('%Y-%m-%d'),

                'month_year': current_date.strftime('%B %Y'),

                'cash_total': float(day_data['cash']),

                'gcash_total': float(day_data['gcash']),

                'total': float(day_data['cash'] + day_data['gcash'])

            })

            current_date += timedelta(days=1)





















    # Top products















    top_products_refill = SaleItem.objects.filter(
        sale__in=sales,
        product__product_type='refill',
    ).values(
        'product_id',
        'product__name',
        'product__container_type',
    ).annotate(
        total_quantity=Sum(F('quantity') - F('returned_quantity')),
        total_revenue=Sum(F('subtotal') - F('returned_amount')),
    ).filter(total_quantity__gt=0).order_by('-total_quantity')

    top_products_gallon = SaleItem.objects.filter(
        sale__in=sales,
        product__product_type='gallon',
    ).values(
        'product_id',
        'product__name',
        'product__container_type',
    ).annotate(
        total_quantity=Sum(F('quantity') - F('returned_quantity')),
        total_revenue=Sum(F('subtotal') - F('returned_amount')),
    ).filter(total_quantity__gt=0).order_by('-total_quantity')































    context = {















        'date_from': start.strftime('%Y-%m-%d'),















        'date_to': end.strftime('%Y-%m-%d'),















        'total_sales': total_sales,















        'total_revenue': total_revenue,
        'delivery_fee_total': delivery_fee_total,















        'average_sale': average_sale,















        'total_items_sold': total_items_sold,















        'payment_methods': payment_methods,















        'cash_total': cash_total,















        'gcash_total': gcash_total,















        'cash_count': cash_count,















        'gcash_count': gcash_count,







        'period': period,







        'sales_data': sales_data,







        'top_products_refill': top_products_refill,









        'top_products_gallon': top_products_gallon,















        'recent_sales': sales,















        'date_range': {
            'start_date': start,
            'end_date': end
        },
        'date_from': start.isoformat(),
        'date_to': end.isoformat(),
        'show_custom_date_range_label': bool(date_from or date_to) and start < end_date,

    }















    return render(request, 'accounts/sales_report.html', context)































@staff_required
@xframe_options_sameorigin
def receipt_view(request, sale_id):















    """View receipt"""















    sale = get_object_or_404(Sale.objects.select_related('customer', 'cashier').prefetch_related('items__product'), id=sale_id)

    order = None
    if sale.order_number:
        order = Order.objects.filter(order_number=sale.order_number).first()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items = [
            {
                'product_name': item.product.name,
                'quantity': item.quantity,
                'subtotal': str(item.subtotal),
            }
            for item in sale.items.all()
        ]
        return JsonResponse({
            'receipt_number': sale.receipt_number,
            'status_display': sale.get_status_display(),
            'items': items,
            'discount': str(order.discount if order else sale.discount),
            'delivery_fee': str(order.delivery_fee if order else Decimal('0.00')),
            'total_amount': str(sale.total_amount),
            'customer_name': (
                sale.customer.get_full_name() or sale.customer.username
                if sale.customer else 'Walk-in'
            ),
            'payment_method_display': sale.get_payment_method_display(),
            'created_at': sale.created_at.isoformat(),
            'delivered_at': order.delivered_at.isoformat() if order and order.delivered_at else None,
        })

    return render(request, 'accounts/receipt.html', {'sale': sale, 'order': order})































@staff_required















def adjust_inventory(request, product_id):















    """Adjust inventory for a specific product"""















    product = get_object_or_404(Product, id=product_id)































    if request.method == 'POST':















        adjustment_type = request.POST.get('adjustment_type')















        quantity = int(request.POST.get('quantity', 0))















        reason = request.POST.get('reason', '')































        if quantity <= 0:















            messages.error(request, 'Quantity must be greater than 0.')















            return redirect('adjust_inventory', product_id=product.id)































        old_stock = product.stock_quantity















        new_stock = old_stock































        if adjustment_type == 'add':















            new_stock = old_stock + quantity















            trans_type = 'purchase'















            qty_change = quantity















        elif adjustment_type == 'remove':















            if quantity > old_stock:















                messages.error(request, f'Cannot remove more than current stock ({old_stock})')















                return redirect('adjust_inventory', product_id=product.id)















            new_stock = old_stock - quantity















            trans_type = 'adjustment'















            qty_change = -quantity















        elif adjustment_type == 'set':















            new_stock = quantity















            trans_type = 'adjustment'















            qty_change = new_stock - old_stock















        else:















            messages.error(request, 'Invalid adjustment type.')















            return redirect('adjust_inventory', product_id=product.id)































        # Update product stock















        product.stock_quantity = new_stock















        product.save()































        # Record inventory transaction















        InventoryTransaction.objects.create(















            product=product,















            transaction_type=trans_type,















            quantity=qty_change,















            previous_stock=old_stock,















            new_stock=new_stock,















            reference=f"Manual adjustment: {reason}" if reason else "Manual adjustment",















            notes=reason,















            created_by=request.user















        )































        messages.success(request, f'Inventory for "{product.name}" adjusted successfully!')















        return redirect('inventory_list')































    context = {















        'product': product,















    }















    return render(request, 'accounts/adjust_inventory.html', context)































@staff_required















def void_sale(request, sale_id):















    """Void/cancel a sale and restore inventory"""















    sale = get_object_or_404(Sale, id=sale_id)































    # Check if sale can be voided















    if sale.status != 'completed':















        messages.error(request, 'Only completed sales can be voided.')















        return redirect('sale_detail', sale_id=sale.id)































    if request.method == 'POST':















        reason = request.POST.get('reason', '')































        if not reason:















            messages.error(request, 'Please provide a reason for voiding the sale.')















            return redirect('sale_detail', sale_id=sale.id)































        with transaction.atomic():















            # Restore inventory for each item















            for item in sale.items.all():















                product = item.product















                old_stock = product.stock_quantity















                product.stock_quantity += item.quantity















                product.save()































                # Record inventory transaction















                InventoryTransaction.objects.create(















                    product=product,















                    transaction_type='return',















                    quantity=item.quantity,















                    previous_stock=old_stock,















                    new_stock=product.stock_quantity,















                    reference=f"Voided sale #{sale.receipt_number}",















                    notes=f"Void reason: {reason}",















                    created_by=request.user















                )































            # Update sale status















            sale.status = 'cancelled'















            sale.notes = f"{sale.notes}\n\nVOIDED on {timezone.now().strftime('%Y-%m-%d %H:%M')} by {request.user.username}. Reason: {reason}"















            sale.save()































            messages.success(request, f'Sale #{sale.receipt_number} has been voided successfully.')































        return redirect('sale_list')































    # If not POST, redirect to sale detail















    return redirect('sale_detail', sale_id=sale.id)































# ===================== PROFILE / USER INFO =====================















from django.contrib.auth.decorators import login_required







from allauth.socialaccount.models import SocialAccount















@login_required







def user_profile(request):







    """







    Display user profile information including Google OAuth details.







    Shows name, email, and profile picture from Google if available.







    """







    user = request.user







    







    # Get social account info (Google)







    social_accounts = SocialAccount.objects.filter(user=user)







    google_account = social_accounts.filter(provider='google').first()







    







    context = {







        'user': user,







        'profile': user.profile if hasattr(user, 'profile') else None,







        'google_account': google_account,







        'is_google_user': google_account is not None,







        'profile_picture': google_account.get_avatar_url() if google_account else None,







        'google_data': google_account.extra_data if google_account else None,







    }







    







    return render(request, 'accounts/profile.html', context)























@login_required







def social_profile_info(request):







    """







    API endpoint to get user's social profile info (for AJAX requests).







    Returns JSON with name, email, picture from Google OAuth.







    """







    user = request.user







    google_account = SocialAccount.objects.filter(user=user, provider='google').first()







    







    data = {







        'authenticated': True,







        'username': user.username,







        'email': user.email,







        'first_name': user.first_name,







        'last_name': user.last_name,







        'full_name': user.get_full_name() or user.username,







        'is_google_user': google_account is not None,







        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),







        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else None,







    }







    







    if google_account:







        extra_data = google_account.extra_data







        data['google'] = {







            'provider': google_account.provider,







            'uid': google_account.uid,







            'picture': extra_data.get('picture'),







            'verified_email': extra_data.get('verified_email'),







            'locale': extra_data.get('locale'),







        }







    







    return JsonResponse(data)















@staff_required

def inventory_reports(request):

    """

    Inventory Reports page with analytics, stock levels, and export capabilities

    Based on the inventory_list.html design pattern

    """

    from django.db.models import Sum, Q, F

    from datetime import datetime, timedelta

    import json

    

    # Get filter parameters

    period = request.GET.get('period', 'daily').lower()
    if period not in ('daily', 'weekly', 'monthly'):
        period = 'daily'
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')

    

    # Inventory reports are limited to Water Gallon products.
    products = Product.objects.filter(
        is_active=True,
        product_type='gallon',
    ).select_related('category')

    

    # Apply search filter if provided

    if search_query:

        products = products.filter(

            Q(name__icontains=search_query) |

            Q(category__name__icontains=search_query) |

            Q(sku__icontains=search_query)

        )

    

    # Calculate summary statistics

    total_products = products.count()

    total_stocks = products.aggregate(total=Sum('stock_quantity'))['total'] or 0

    low_stock_items = products.filter(stock_quantity__lte=F('reorder_level'), stock_quantity__gt=0).count()

    out_of_stock_items = products.filter(stock_quantity=0).count()

    

    # Prepare product data for the table

    product_data = []

    for product in products:

        # Determine stock status

        if product.stock_quantity <= 0:

            status = 'out'

            status_display = 'Out of Stock'

            status_class = 'out'

        elif product.stock_quantity <= product.reorder_level:

            status = 'low'

            status_display = 'Low Stock'

            status_class = 'low'

        else:

            status = 'available'

            status_display = 'Available'

            status_class = 'available'

        

        product_data.append({

            'id': product.id,

            'name': product.name,

            'category': product.category.name if product.category else 'Uncategorized',

            'stock_quantity': product.stock_quantity,

            'reorder_level': product.reorder_level,

            'is_low_stock': product.is_low_stock,

            'status': status,

            'status_display': status_display,

            'status_class': status_class,

        })



    # Prepare all-product labels/values for charts (show all product names)

    all_product_labels = [p.name for p in products]

    all_product_values = [p.stock_quantity for p in products]



    

    # Set up date range for transactions

    end_date = timezone.localdate()
    start_date = _report_period_default_start(period, end_date)

    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:

            pass

    

    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    

    # Get inventory transactions for history

    transactions = InventoryTransaction.objects.filter(
        product__product_type='gallon',
        created_at__date__gte=start_date,

        created_at__date__lte=end_date

    ).select_related('product', 'created_by').order_by('-created_at')[:50]

    

    # Prepare chart data - Category distribution (stock quantities by category)

    category_data = {}

    for product in products:

        cat_name = product.category.name if product.category else 'Uncategorized'

        category_data[cat_name] = category_data.get(cat_name, 0) + product.stock_quantity

    

    category_labels = list(category_data.keys())

    category_values = list(category_data.values())



    # Prepare top product-level data for the 'Stock Levels by Product' chart

    top_products = product_data[:10]

    product_labels = [p['name'] for p in top_products]

    product_values = [p['stock_quantity'] for p in top_products]

    

    # Prepare monthly movement data (last 6 months)

    monthly_labels = []

    stock_in_data = []

    stock_out_data = []

    

    for i in range(5, -1, -1):

        month_date = timezone.now().date() - timedelta(days=30 * i)

        month_label = month_date.strftime('%b %Y')

        monthly_labels.append(month_label)

        

        # Get month start and end

        month_start = month_date.replace(day=1)

        if month_date.month == 12:

            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)

        else:

            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

        

        # Count stock in transactions (purchase, return, adjustment with positive quantity)

        stock_in = InventoryTransaction.objects.filter(
            product__product_type='gallon',
            created_at__date__gte=month_start,

            created_at__date__lte=month_end,

            quantity__gt=0

        ).aggregate(total=Sum('quantity'))['total'] or 0

        

        # Count stock out transactions (sale, damage, adjustment with negative quantity)

        stock_out = InventoryTransaction.objects.filter(
            product__product_type='gallon',
            created_at__date__gte=month_start,

            created_at__date__lte=month_end,

            quantity__lt=0

        ).aggregate(total=Sum('quantity'))['total'] or 0

        

        stock_in_data.append(stock_in)

        stock_out_data.append(abs(stock_out))

    

    context = {

        'products': product_data,

        'transactions': transactions,

        'total_products': total_products,

        'total_stocks': total_stocks,

        'low_stock_items': low_stock_items,

        'out_of_stock_items': out_of_stock_items,

        'search_query': search_query,

        'date_from': start_date.strftime('%Y-%m-%d'),

        'date_to': end_date.strftime('%Y-%m-%d'),

        'period': period,

        'category_labels': json.dumps(category_labels),

        'category_values': json.dumps(category_values),

        'product_labels': json.dumps(product_labels),

        'product_values': json.dumps(product_values),

        'all_product_labels': json.dumps(all_product_labels),

        'all_product_values': json.dumps(all_product_values),

        'monthly_labels': json.dumps(monthly_labels),

        'stock_in_data': json.dumps(stock_in_data),

        'stock_out_data': json.dumps(stock_out_data),

    }

    

    return render(request, 'accounts/inventory_reports.html', context)





# ==================== MAINTENANCE VIEWS ====================

# Add these imports at the top





# ===================== MAINTENANCE VIEWS =====================




@admin_required

def maintenance_reports(request):

    """Maintenance Reports Log page"""

    return render(request, 'accounts/maintenance_reports.html')



@admin_required

def maintenance_view(request):

    """Maintenance management page"""

    return render(request, 'accounts/maintenance.html')





@admin_required

def get_maintenance_tasks(request):

    """API endpoint to get all maintenance tasks"""

    tasks = MaintenanceTask.objects.exclude(status='Completed')

    tasks_data = []

    

    for task in tasks:

        tasks_data.append({

            'id': task.id,

            'task': task.title,

            'description': task.description or '',

            'date': task.scheduled_date.strftime('%Y-%m-%d'),

            'time': task.scheduled_time.strftime('%H:%M') if task.scheduled_time else '',

            'status': 'Pending' if task.status == 'Scheduled' else task.status,

        })

    

    return JsonResponse({'success': True, 'tasks': tasks_data})





@admin_required

def get_maintenance_reports(request):

    """API endpoint to get all maintenance reports"""

    # Keep every report in the log, including Resolved and Closed reports.
    reports = MaintenanceReport.objects.select_related(
        'reported_by',
        'resolved_by',
    ).prefetch_related('photos').order_by('-created_at')
    # A completed task's updated_at reflects when it was moved to Completed.
    completed_tasks = MaintenanceTask.objects.filter(
        status='Completed'
    ).select_related('completed_by').order_by('-updated_at', '-scheduled_date', '-scheduled_time')

    reports_data = []
    completed_tasks_data = []

    

    for report in reports:

        reports_data.append({

            'id': report.id,

            'category': report.category,

            'description': report.description,

            'due_date': report.due_date.isoformat() if report.due_date else '',

            'photo_urls': [
                request.build_absolute_uri(photo.image.url)
                for photo in report.photos.all()
            ] or ([request.build_absolute_uri(report.photo.url)] if report.photo else []),

            'priority': report.priority,

            'status': report.status,

            'date': report.created_at.strftime('%Y-%m-%d %H:%M'),
            'reported_by': report.reported_by.username if report.reported_by else 'System',
            'staff_name': (
                report.resolved_by.get_full_name() or report.resolved_by.username
                if report.resolved_by else ''
            ),

        })

    for task in completed_tasks:
        completed_tasks_data.append({
            'id': task.id,
            'task': task.title,
            'description': task.description or '',
            'date': task.scheduled_date.strftime('%Y-%m-%d'),
            'time': task.scheduled_time.strftime('%H:%M') if task.scheduled_time else '',
            'status': task.status,
            'staff_name': (
                task.completed_by.get_full_name() or task.completed_by.username
                if task.completed_by else ''
            ),
            'completed_at': task.updated_at.strftime('%Y-%m-%d %H:%M'),
        })

    

    return JsonResponse({
        'success': True,
        'reports': reports_data,
        'completed_tasks': completed_tasks_data,
    })





@admin_required

@require_http_methods(["POST"])

def create_maintenance_task(request):

    """Create a new maintenance task"""

    try:

        data = json.loads(request.body)

        scheduled_date = parse_date(data.get('date', ''))
        if scheduled_date is None:
            return JsonResponse({
                'success': False,
                'message': 'Please select a valid schedule date.'
            }, status=400)
        if scheduled_date < timezone.localdate():
            return JsonResponse({
                'success': False,
                'message': 'Cleaning schedules cannot be set for a past date.'
            }, status=400)

        title = (data.get('title') or '').strip()
        if not title:
            return JsonResponse({
                'success': False,
                'message': 'Please provide a maintenance task.'
            }, status=400)
        
        task = MaintenanceTask.objects.create(

            title=title,

            description=data.get('description', ''),

            assigned_to=data.get('assigned_to'),

            scheduled_date=scheduled_date,

            scheduled_time=None,

            created_by=request.user,

            status='Pending'

        )

        

        return JsonResponse({

            'success': True,

            'message': 'Task created successfully',

            'task_id': task.id

        })

        

    except Exception as e:

        return JsonResponse({

            'success': False,

            'message': str(e)

        }, status=400)





def _validate_maintenance_report_photos(photos):
    for photo in photos:
        if photo.size > 5 * 1024 * 1024:
            return 'Photo must be 5 MB or smaller.'
        if photo.content_type not in {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}:
            return 'Upload a JPEG, PNG, WEBP, or GIF image.'
        try:
            image = Image.open(photo)
            image.verify()
            photo.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            return 'The uploaded file is not a valid image.'
    return None


def _save_maintenance_report_photos(report, photos):
    for photo in photos:
        image = Image.open(photo)
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        compressed = BytesIO()
        image.save(
            compressed,
            format='JPEG',
            quality=65,
            optimize=True,
            progressive=True,
            subsampling=2,
        )
        maintenance_photo = MaintenanceReportPhoto.objects.create(report=report)
        maintenance_photo.image.save(
            f'{uuid4().hex}.jpg',
            ContentFile(compressed.getvalue()),
            save=True,
        )


@admin_required
@require_http_methods(["POST"])
def upload_maintenance_report_photos(request, report_id):
    report = get_object_or_404(MaintenanceReport, id=report_id)
    photos = request.FILES.getlist('photos')
    if not photos:
        return JsonResponse(
            {'success': False, 'message': 'Please select at least one photo.'},
            status=400,
        )

    error = _validate_maintenance_report_photos(photos)
    if error:
        return JsonResponse({'success': False, 'message': error}, status=400)

    _save_maintenance_report_photos(report, photos)
    report.save(update_fields=['updated_at'])
    return JsonResponse({'success': True, 'message': 'Photos uploaded successfully.'})


@admin_required
@require_http_methods(["POST"])
def create_maintenance_report(request):

    """Create a new maintenance report"""

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {'success': False, 'message': 'Invalid report data.'},
                status=400,
            )
        if not isinstance(data, dict):
            return JsonResponse(
                {'success': False, 'message': 'Invalid report data.'},
                status=400,
            )
    else:
        data = request.POST

    category = str(data.get('category', '')).strip()
    description = str(data.get('description', '')).strip()
    priority = str(data.get('priority', 'Medium')).strip()
    due_date = parse_date(str(data.get('due_date', '') or ''))
    photos = request.FILES.getlist('photos')
    if not photos and request.FILES.get('photo'):
        photos = [request.FILES['photo']]

    valid_categories = {value for value, _label in MaintenanceReport.CATEGORY_CHOICES}
    valid_priorities = {value for value, _label in MaintenanceReport.PRIORITY_CHOICES}
    if category not in valid_categories:
        return JsonResponse({'success': False, 'message': 'Please choose a valid maintenance category.'}, status=400)
    if priority not in valid_priorities:
        return JsonResponse({'success': False, 'message': 'Please choose a valid priority.'}, status=400)
    if due_date is None:
        return JsonResponse({'success': False, 'message': 'Please provide a valid due date.'}, status=400)
    if due_date < timezone.localdate():
        return JsonResponse({'success': False, 'message': 'Due date cannot be in the past.'}, status=400)

    error = _validate_maintenance_report_photos(photos)
    if error:
        return JsonResponse({'success': False, 'message': error}, status=400)

    report = MaintenanceReport.objects.create(
        category=category,
        description=description,
        due_date=due_date,
        priority=priority,
        status='Open',
        reported_by=request.user,
    )
    if photos:
        _save_maintenance_report_photos(report, photos)

    return JsonResponse({
        'success': True,
        'message': 'Report created successfully',
        'report_id': report.id,
        'report': {
            'id': report.id,
            'category': report.category,
            'description': report.description,
            'due_date': report.due_date.isoformat() if report.due_date else '',
            'photo_urls': [],
            'priority': report.priority,
            'status': report.status,
            'date': report.created_at.strftime('%Y-%m-%d %H:%M'),
            'reported_by': request.user.username,
            'staff_name': '',
        },
    })





@admin_required

@require_http_methods(["DELETE"])

def delete_maintenance_task(request, task_id):

    """Delete a maintenance task"""

    try:

        task = get_object_or_404(MaintenanceTask, id=task_id)

        task.delete()

        return JsonResponse({'success': True, 'message': 'Task deleted successfully'})

    except Exception as e:

        return JsonResponse({'success': False, 'message': str(e)}, status=400)





@admin_required

@require_http_methods(["DELETE"])

def delete_maintenance_report(request, report_id):

    """Delete a maintenance report"""

    try:

        report = get_object_or_404(MaintenanceReport, id=report_id)

        report.delete()

        return JsonResponse({'success': True, 'message': 'Report deleted successfully'})

    except Exception as e:

        return JsonResponse({'success': False, 'message': str(e)}, status=400)





@staff_required

@require_http_methods(["PUT"])

def update_maintenance_task_status(request, task_id):

    """Update task status"""

    try:

        data = json.loads(request.body)

        task = get_object_or_404(MaintenanceTask, id=task_id)

        incoming_status = data.get('status')
        status_map = {
            'Pending': 'Pending',
            'Scheduled': 'Pending',
            'In Progress': 'In Progress',
            'Completed': 'Completed',
            'Cancelled': 'Cancelled',
        }

        if incoming_status not in status_map:
            return JsonResponse({'success': False, 'message': 'Invalid status value.'}, status=400)

        task.status = status_map[incoming_status]
        if task.status == 'Completed':
            task.completed_by = request.user

        task.save()

        return JsonResponse({'success': True, 'message': 'Status updated successfully'})

    except Exception as e:

        return JsonResponse({'success': False, 'message': str(e)}, status=400)





@staff_required

@require_http_methods(["PUT"])

def update_maintenance_report_status(request, report_id):

    """Update report status"""

    try:

        data = json.loads(request.body)

        report = get_object_or_404(MaintenanceReport, id=report_id)

        old_status = report.status
        incoming_status = data.get('status')

        status_map = {
            'Pending': 'Open',
            'Open': 'Open',
            'In Progress': 'In Progress',
            'Resolved': 'Resolved',
            'Closed': 'Closed',
        }

        if incoming_status not in status_map:
            return JsonResponse({'success': False, 'message': 'Invalid status value.'}, status=400)

        report.status = status_map[incoming_status]

        

        if report.status == 'Resolved' and old_status != 'Resolved':

            report.resolved_by = request.user

            report.resolved_at = timezone.now()

        

        if data.get('resolution_notes'):

            report.resolution_notes = data.get('resolution_notes')

        

        report.save()

        

        return JsonResponse({'success': True, 'message': 'Status updated successfully'})

    except Exception as e:

        return JsonResponse({'success': False, 'message': str(e)}, status=400)

# ===================== EMAIL VERIFICATION HELPER =====================



# ===================== EMAIL VERIFICATION HELPER =====================



def send_verification_email(email, code):

    """Send OTP verification email to user's email"""

    from django.core.mail import send_mail

    from django.conf import settings

    

    subject = 'Verify Your Email - Grateful Water Station'

    

    html_message = f"""

    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <title>Email Verification - Grateful Water Station</title>

        <style>

            body {{ font-family: Arial, sans-serif; }}

            .container {{ max-width: 500px; margin: 0 auto; padding: 20px; }}

            .header {{ background: #0ea5e9; padding: 20px; text-align: center; color: white; border-radius: 12px 12px 0 0; }}

            .code {{ font-size: 32px; font-weight: bold; text-align: center; padding: 20px; background: #f0f9ff; margin: 20px 0; letter-spacing: 5px; border-radius: 8px; }}

            .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}

        </style>

    </head>

    <body>

        <div class="container">

            <div class="header">

                <h2>Grateful Water Station</h2>

            </div>

            <div class="content">

                <p>Hello,</p>

                <p>Your verification code is:</p>

                <div class="code">{code}</div>

                <p>This code will expire in 5 minutes.</p>

            </div>

            <div class="footer">

                <p>Grateful Water Station - Premium Water Delivery</p>

            </div>

        </div>

    </body>

    </html>

    """

    

    plain_message = f"Your verification code is: {code}\n\nThis code expires in 5 minutes."

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.error(
            "Email verification is not configured; set EMAIL_HOST_USER and "
            "EMAIL_HOST_PASSWORD in the environment."
        )
        return False

    try:

        sent_count = send_mail(

            subject,

            plain_message,

            settings.DEFAULT_FROM_EMAIL,

            [email],

            fail_silently=False,

            html_message=html_message

        )

        if sent_count != 1:
            logger.error("Email backend did not send the verification email to %s.", email)
            return False
        logger.info("Sent email verification code to %s.", email)
        return True

    except Exception:

        logger.exception("Failed to send email verification code to %s.", email)
        return False





def email_verification_view(request):

    """Show OTP verification page"""

    pending_email = request.session.get('pending_email')

    if not pending_email:

        messages.error(request, 'No pending registration found. Please register first.')

        return redirect('register')

    return render(request, 'accounts/email_verification.html', {'email': pending_email})





from django.views.decorators.http import require_http_methods

import json





@require_http_methods(["POST"])

def verify_email_otp(request):

    """Verify OTP and create user account"""

    print("[DEBUG] verify_email_otp called")

    

    try:

        # Parse JSON data

        data = json.loads(request.body)

        otp = data.get('otp', '').strip()

        
        
        # Get session data

        pending_email = request.session.get('pending_email')

        pending_data = request.session.get('pending_registration')

        

        print(f"[DEBUG] Pending email: {pending_email}")

        print(f"[DEBUG] Pending data exists: {pending_data is not None}")

        

        # Validate session data

        if not pending_email or not pending_data:

            return JsonResponse({

                'success': False, 

                'message': 'Registration session expired. Please register again.'

            })

        

        # Find verification record

        try:

            verification = EmailVerification.objects.get(

                email=pending_email, 

                is_verified=False

            )
        except EmailVerification.DoesNotExist:

            print(f"[DEBUG] No verification record found for {pending_email}")

            return JsonResponse({

                'success': False, 

                'message': 'Verification code not found. Please register again.'

            })

        

        # Check if expired

        if verification.is_expired():

            print(f"[DEBUG] Code expired")

            verification.delete()

            return JsonResponse({

                'success': False, 

                'message': 'Verification code has expired. Please register again.'

            })

        

        # Verify the code

        if verification.verification_code != otp:

            verification.attempts += 1

            verification.save()

            remaining = 5 - verification.attempts

            print(f"[DEBUG] Wrong code. Attempts: {verification.attempts}")

            if remaining <= 0:

                verification.delete()

                return JsonResponse({

                    'success': False, 

                    'message': 'Too many failed attempts. Please register again.'

                })

            return JsonResponse({

                'success': False, 

                'message': f'Invalid code. {remaining} attempt(s) remaining.'

            })

        

        print(f"[DEBUG] Code verified successfully!")

        

        # Code is correct - create user account

        from django.contrib.auth.hashers import make_password

        

        # Check if user already exists

        if User.objects.filter(username=pending_data['username']).exists():

            return JsonResponse({

                'success': False, 

                'message': 'Username already taken. Please register again.'

            })

        

        if User.objects.filter(email=pending_data['email']).exists():

            return JsonResponse({

                'success': False, 

                'message': 'Email already registered. Please login instead.'

            })

        

        # Create user - FIXED INDENTATION

        user = User.objects.create(

            username=pending_data['username'],

            email=pending_data['email'],

            first_name=pending_data['first_name'],

            last_name=pending_data['last_name'],

            password=make_password(pending_data['password'])

        )

        print(f"[DEBUG] User created: {user.username}")

        

        # Create or update profile (signal may have already created it)

        try:

            profile = user.profile

        except UserProfile.DoesNotExist:

            profile = UserProfile.objects.create(user=user)

        

        profile.phone_number = pending_data['phone_number']
        profile.address = pending_data['address']
        profile.role = 'customer'
        profile.default_latitude = pending_data.get('default_latitude')
        profile.default_longitude = pending_data.get('default_longitude')
        profile.save()

        print(f"[DEBUG] Profile updated for: {user.username}")

        

        # Create Consumer record

        Consumer.objects.get_or_create(user=user)

        print(f"[DEBUG] Consumer created for: {user.username}")

        

        # Mark as verified and clean up

        verification.is_verified = True

        verification.save()

        

        # Clear session

        request.session.pop('pending_email', None)

        request.session.pop('pending_registration', None)

        

        # Login user with backend specified

        from django.contrib.auth import login

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        print(f"[DEBUG] User logged in: {user.username}")

        

        return JsonResponse({

            'success': True, 

            'message': 'Email verified successfully! Redirecting...', 

            'redirect_url': reverse('customer_dashboard')

        })

        

    except json.JSONDecodeError as e:

        print(f"[ERROR] JSON decode error: {e}")

        return JsonResponse({

            'success': False, 

            'message': 'Invalid request format.'

        })

    except Exception as e:

        print(f"[ERROR] Verification error: {str(e)}")

        import traceback

        traceback.print_exc()

        return JsonResponse({

            'success': False, 

            'message': f'An error occurred: {str(e)}'

        })





@require_http_methods(["POST"])

def resend_verification_otp(request):

    """Resend OTP to email"""

    try:

        pending_email = request.session.get('pending_email')

        

        if not pending_email:

            return JsonResponse({

                'success': False, 

                'message': 'No pending registration found. Please register again.'

            })

        

        # Delete old unverified records

        EmailVerification.objects.filter(email=pending_email, is_verified=False).delete()

        

        # Create new verification record

        verification = EmailVerification.create_for_email(pending_email)

        
        # Send email

        email_sent = send_verification_email(pending_email, verification.verification_code)

        

        if email_sent:

            return JsonResponse({

                'success': True, 

                'message': f'A new verification code has been sent to {pending_email}.'

            })

        else:

            verification.delete()

            return JsonResponse({

                'success': False, 

                'message': 'Email could not be sent. Please check the email server configuration and try again.'

            })

    except Exception as e:

        print(f"[ERROR] Resend error: {str(e)}")

        return JsonResponse({

            'success': False, 

            'message': 'An error occurred. Please try again.'

        })





# Customer registration without email verification.

def register_view(request):

    """Create and sign in a customer without email verification."""

    if request.user.is_authenticated:

        return redirect('dashboard_redirect')

    print("[DEBUG] register_view called")

    

    if request.method == 'POST':

        form = EmailRegistrationForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=data['username'],
                        email=data['email'],
                        password=data['password1'],
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                    )
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    user.profile = profile
                    profile.phone_number = data['phone_number']
                    profile.address = data['address']
                    profile.role = 'customer'
                    profile.default_latitude = data.get('default_latitude')
                    profile.default_longitude = data.get('default_longitude')
                    profile.save()
                    Consumer.objects.get_or_create(user=user)
            except IntegrityError:
                form.add_error(
                    None,
                    'That username or email is already in use. Please choose another or sign in.',
                )
                return render(request, 'accounts/register.html', {'form': form})

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully.')
            return redirect('customer_dashboard')

        else:

            print(f"[DEBUG] Form errors: {form.errors}")

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, f'{field}: {error}')

    else:

        form = EmailRegistrationForm()

    

    return render(request, 'accounts/register.html', {'form': form})