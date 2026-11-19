from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone
import random
import string
from decimal import Decimal
import uuid


# ==================== POS MODELS ====================

class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class AdminAnnouncementImage(models.Model):
    CATEGORY_CHOICES = (
        ('important', 'Important Announcement'),
        ('promo', 'Promo / Discount'),
        ('new_product', 'New Product / Service'),
        ('hours', 'Schedule / Operating Hours'),
        ('delivery', 'Delivery Updates'),
        ('featured', 'Featured Product'),
        ('offer', 'Special Offer'),
        ('store_info', 'Store Information'),
        ('reminder', 'Customer Reminder'),
    )

    image = models.ImageField(upload_to='admin_announcements/', blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='important')
    headline = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=280, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f"Admin announcement {self.id}"


class WifiConfiguration(models.Model):
    """Wi-Fi credentials retrieved by the station controller."""
    ssid = models.CharField(max_length=100)
    password = models.CharField(max_length=128)
    device_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wi-Fi configuration"
        verbose_name_plural = "Wi-Fi configuration"

    def __str__(self):
        return self.ssid


class Product(models.Model):
    """Products available for sale"""
    WATER_TYPES = (
        ('mineral', 'Mineral Water'),
    )

    CONTAINER_TYPES = (
        ('bottle_350ml', 'Gallon Slim Containerer'),
        ('gallon', 'Gallon Blue Water Container'),
        ('container_5g', 'Blue Water Dispens Round Container'),
        ('distilled', 'Grateful Purified Water'),
    )

    PRODUCT_TYPES = (
        ('refill', 'Water Refill'),
        ('gallon', 'Water Gallon'),
    )

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    water_type = models.CharField(max_length=20, choices=WATER_TYPES, default='mineral')
    container_type = models.CharField(max_length=20, choices=CONTAINER_TYPES, default='gallon')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='refill')
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - ₱{self.price}"

    def save(self, *args, **kwargs):
        if not self.sku:
            prefix = ''.join([c for c in self.name[:3].upper() if c.isalpha()])
            if not prefix:
                prefix = 'PRD'
            random_num = ''.join(random.choices(string.digits, k=5))
            self.sku = f"{prefix}{random_num}"
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level

    def get_main_image(self):
        """Get the main product image URL"""
        first_image = self.images.first()
        if first_image:
            return first_image.image.url
        return None


class ProductImage(models.Model):
    """Product images for gallery"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # If this is the first image, make it main
        if not self.product.images.exists():
            self.is_main = True
        super().save(*args, **kwargs)


class Sale(models.Model):
    """POS Transaction"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
    )

    SALE_STATUS = (
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    ORDER_TYPES = (
        ('walkin', 'Walk-in / Pick-up'),
        ('delivery', 'Delivery'),
    )

    receipt_number = models.CharField(max_length=50, unique=True)
    order_number = models.CharField(max_length=50, blank=True, null=True, help_text="Original order number if this sale came from a delivery order")
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_purchases',
        limit_choices_to={'profile__role': 'customer'}
    )
    cashier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_sales'
    )
    rider = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_deliveries',
        limit_choices_to={'profile__role': 'rider'}
    )
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPES,
        default='walkin'
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    returned_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=SALE_STATUS, default='completed')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        customer_name = self.customer.get_full_name() or self.customer.username if self.customer else 'Walk-in Customer'
        return f"{self.receipt_number} - {customer_name} - ₱{self.total_amount}"

    @property
    def net_amount(self):
        return max(Decimal('0.00'), self.total_amount - self.returned_amount)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from django.utils import timezone
            today = timezone.now().strftime('%Y%m%d')
            last_sale = Sale.objects.filter(
                receipt_number__startswith=f'REC-{today}'
            ).order_by('-receipt_number').first()

            if last_sale:
                last_num = int(last_sale.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.receipt_number = f'REC-{today}-{new_num:04d}'

        if self.amount_paid > self.total_amount:
            self.change_amount = self.amount_paid - self.total_amount
        else:
            self.change_amount = 0

        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """Individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    order_item = models.ForeignKey(
        'OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sale_items',
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    returned_quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    returned_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def kept_quantity(self):
        return max(0, self.quantity - self.returned_quantity)

    @property
    def net_subtotal(self):
        return max(Decimal('0.00'), self.subtotal - self.returned_amount)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class InventoryTransaction(models.Model):
    """Track inventory movements"""
    TRANSACTION_TYPES = (
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('damage', 'Damage/Loss'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity})"


# ==================== ACCOUNTS MODELS ====================

class UserProfile(models.Model):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('rider', 'Rider'),
        ('customer', 'Customer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, default='')
    address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add these missing fields that exist in your database
    block = models.BooleanField(default=False)
    street = models.CharField(max_length=255, blank=True, null=True)  # Add this
    city = models.CharField(max_length=100, blank=True, null=True)    # Add this if exists
    zip_code = models.CharField(max_length=20, blank=True, null=True) # Add this if exists
    
    # Default location from last map picker use
    default_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    default_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notifications_read_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consumer')
    total_orders = models.IntegerField(default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Consumer: {self.user.username}"

class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Order(models.Model):
    ORDER_STATUS = (
        ('awaiting_payment', 'Awaiting Payment'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('send-to-rider', 'Send to Rider'),
        ('rider_accepted', 'Rider Accepted'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHODS = (
        ('cod', 'Cash on Delivery'),
        ('gcash', 'GCash'),
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', limit_choices_to={'profile__role': 'customer'})
    rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries', limit_choices_to={'profile__role': 'rider'})
    order_number = models.CharField(max_length=20, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_distance_km = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    delivery_area = models.CharField(max_length=100, default='Talon 3')
    delivery_fee_requires_approval = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    delivery_address = models.TextField()
    delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Delivery fields
    delivery_image = models.ImageField(upload_to='', blank=True, null=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cod')
    
    # Map coordinates from Leaflet picker
    delivery_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    @property
    def has_coordinates(self):
        return self.delivery_lat is not None and self.delivery_lng is not None

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"


class ReturnRequest(models.Model):
    REASON_CHOICES = (
        ('damaged', 'Damaged item'),
        ('wrong_item', 'Wrong item received'),
        ('quality_issue', 'Quality issue'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    PICKUP_STATUS_CHOICES = (
        ('not_ready', 'Not ready for pickup'),
        ('awaiting_assignment', 'Awaiting rider assignment'),
        ('assigned', 'Rider assigned'),
        ('picked_up', 'Picked up'),
        ('payment_returned', 'Payment Returned'),
        ('received', 'Returned to station'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    evidence_image = models.ImageField(upload_to='return_evidence/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_return_requests',
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    pickup_status = models.CharField(
        max_length=24,
        choices=PICKUP_STATUS_CHOICES,
        default='not_ready',
    )
    pickup_rider = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_return_pickups',
        limit_choices_to={'profile__role': 'rider'},
    )
    picked_up_at = models.DateTimeField(null=True, blank=True)
    payment_returned_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    inspected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_return_requests',
    )
    inspected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return request for {self.order.order_number} ({self.status})"


class ReturnRequestItem(models.Model):
    return_request = models.ForeignKey(
        ReturnRequest,
        on_delete=models.CASCADE,
        related_name='items',
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name='return_items',
    )
    quantity = models.PositiveIntegerField()
    restockable_quantity = models.PositiveIntegerField(null=True, blank=True)
    sales_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('return_request', 'order_item'),
                name='unique_return_request_order_item',
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.order_item.product.name} for {self.return_request.order.order_number}"


class ReturnRequestImage(models.Model):
    return_request = models.ForeignKey(
        ReturnRequest,
        on_delete=models.CASCADE,
        related_name='evidence_images',
    )
    image = models.ImageField(upload_to='return_evidence/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']


# Signal handlers
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        try:
            UserProfile.objects.create(
                user=instance,
                block=False,   # ← was '' — must be False for BooleanField
                street=''
            )
        except Exception as e:
            print(f"Error creating profile for user {instance.username}: {e}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, raw=False, **kwargs):
    if raw:
        return
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Exception as e:
        print(f"Error saving profile for user {instance.username}: {e}")

class Conversation(models.Model):
    """A conversation between two or more users"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        names = ', '.join(u.get_full_name() or u.username for u in self.participants.all()[:3])
        return f"Conversation: {names}"

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """A single message within a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class ContactMessage(models.Model):
    """A message submitted by a visitor from the public contact form."""
    recipient = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contact_messages',
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


# ==================== MAINTENANCE MODELS ====================

class MaintenanceTask(models.Model):
    """Scheduled maintenance tasks"""
    
    RECURRENCE_CHOICES = (
        ('One-time', 'One-time'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
    )
    
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(blank=True, null=True)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='One-time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_maintenance_tasks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_date}"


class MaintenanceReport(models.Model):
    """Maintenance issue reports"""
    
    CATEGORY_CHOICES = (
        ('Filter System', 'Filter System'),
        ('Water Pump', 'Water Pump'),
        ('Pipes & Fittings', 'Pipes & Fittings'),
        ('Electrical', 'Electrical'),
        ('Dispenser Unit', 'Dispenser Unit'),
        ('Other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    )
    
    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    due_date = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='maintenance_reports/', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    resolution_notes = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_issues')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues')
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.category} - {self.status} ({self.created_at.strftime('%Y-%m-%d')})"


class MaintenanceReportPhoto(models.Model):
    report = models.ForeignKey(
        MaintenanceReport,
        on_delete=models.CASCADE,
        related_name='photos',
    )
    image = models.ImageField(upload_to='maintenance_reports/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f"Photo for maintenance report {self.report_id}"
    
    def mark_resolved(self, user, notes=None):
        self.status = 'Resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save()
# Add this after the MaintenanceReport model
class EmailVerification(models.Model):
    """Email verification with OTP code"""
    email = models.EmailField()
    verification_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Verification for {self.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_for_email(email):
        """Create or update verification code for email"""
        # Delete any existing unverified entries for this email
        EmailVerification.objects.filter(email=email, is_verified=False).delete()
        
        code = EmailVerification.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=5)  # 5 minutes expiry
        
        verification = EmailVerification.objects.create(
            email=email,
            verification_code=code,
            expires_at=expires_at,
            attempts=0
        )
        
        return verification
    
    def verify(self, code):
        """Verify the provided code"""
        if self.is_expired():
            return False, "Verification code has expired. Please request a new one."
        
        if self.attempts >= 5:
            return False, "Too many failed attempts. Please request a new verification code."
        
        self.attempts += 1
        self.save()
        
        if code.strip() == self.verification_code:
            self.is_verified = True
            self.save()
            return True, "Email verified successfully!"
        
        remaining = 5 - self.attempts
        return False, f"Invalid code. {remaining} attempt(s) remaining."


class Notification(models.Model):
    """Persistent in-app notification for the authenticated user."""

    CATEGORY_CHOICES = (
        ('orders', 'Orders'),
        ('announcement', 'Announcement'),
        ('inventory', 'Inventory'),
        ('maintenance', 'IoT/Maintenance'),
        ('riders', 'Riders'),
        ('users', 'Users'),
    )
    SEVERITY_CHOICES = (
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_notifications')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='orders')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    target_url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.recipient})'


class StationAvailability(models.Model):
    """Singleton-style setting shared by admin and customer dashboards."""

    is_open = models.BooleanField(default=True)
    delivery_fee_up_to_2km = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    delivery_fee_up_to_3km = models.DecimalField(max_digits=10, decimal_places=2, default=30)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Open' if self.is_open else 'Closed'

