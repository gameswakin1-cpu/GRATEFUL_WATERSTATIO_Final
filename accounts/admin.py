from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, Consumer, Order, Conversation, Message, ContactMessage,
    Category, Product, Sale, SaleItem, InventoryTransaction,
    MaintenanceTask, MaintenanceReport, AdminAnnouncementImage  # Add these imports
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    max_num = 1
    min_num = 0
    
    def get_extra(self, request, obj=None, **kwargs):
        return 1 if obj is None else 0

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('profile__role', 'is_staff', 'is_superuser', 'is_active')
    
    def get_role(self, obj):
        try:
            return obj.profile.role
        except (UserProfile.DoesNotExist, AttributeError):
            return 'No Profile'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, UserProfile):
                instance.user = form.instance
            instance.save()
        for instance in formset.deleted_objects:
            instance.delete()
        formset.save_m2m()

# Unregister the old User admin and register the new one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(AdminAnnouncementImage)
class AdminAnnouncementImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_orders', 'last_order_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__email')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'rider', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('order_number', 'customer__username', 'customer__first_name', 'customer__last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'total_amount')
        }),
        ('Delivery Details', {
            'fields': ('delivery_address', 'delivery_lat', 'delivery_lng', 'rider')
        }),
        ('Status & Payment', {
            'fields': ('status', 'payment_method', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'message_count', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('participants__username', 'participants__first_name', 'participants__last_name')
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_participants(self, obj):
        return ", ".join([f"{p.get_full_name() or p.username} ({p.profile.role})" for p in obj.participants.all()])
    get_participants.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    fieldsets = (
        ('Conversation Details', {
            'fields': ('participants', 'is_active')
        }),
        ('Statistics', {
            'fields': ('message_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_sender_info', 'get_conversation_info', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'conversation__is_active')
    search_fields = ('content', 'sender__username', 'sender__first_name', 'sender__last_name')
    readonly_fields = ('created_at',)
    list_select_related = ('sender', 'conversation')
    
    def get_sender_info(self, obj):
        role = obj.sender.profile.role if hasattr(obj.sender, 'profile') else 'unknown'
        return f"{obj.sender.get_full_name() or obj.sender.username} ({role})"
    get_sender_info.short_description = 'Sender'
    get_sender_info.admin_order_field = 'sender__username'
    
    def get_conversation_info(self, obj):
        participants = obj.conversation.participants.all()
        return f"Conv #{obj.conversation.id} - {participants.count()} participant(s)"
    get_conversation_info.short_description = 'Conversation'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Message Preview'
    
    fieldsets = (
        ('Message Details', {
            'fields': ('conversation', 'sender', 'content', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected_messages']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} message(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'
    
    def delete_selected_messages(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} message(s) deleted successfully.')
    delete_selected_messages.short_description = 'Delete selected messages'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'recipient')
    search_fields = ('name', 'email', 'phone', 'content')
    readonly_fields = ('created_at',)
    list_select_related = ('recipient',)
    ordering = ('-created_at',)
    actions = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        ('Visitor Details', {
            'fields': ('name', 'email', 'phone', 'content')
        }),
        ('Administration', {
            'fields': ('recipient', 'is_read', 'created_at')
        }),
    )

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} contact message(s) marked as read.')
    mark_as_read.short_description = 'Mark selected contact messages as read'

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} contact message(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected contact messages as unread'


# ==================== POS ADMIN ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_low_stock', 'is_active']
    list_filter = ['category', 'water_type', 'container_type', 'is_active']
    search_fields = ['name', 'sku', 'barcode']
    list_editable = ['price', 'stock_quantity', 'is_active']

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    readonly_fields = ['product', 'quantity', 'unit_price', 'subtotal']
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'customer', 'cashier', 'total_amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['receipt_number', 'customer__username']
    readonly_fields = ['receipt_number', 'subtotal', 'total_amount', 'change_amount']
    inlines = [SaleItemInline]
    date_hierarchy = 'created_at'

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'transaction_type', 'quantity', 'previous_stock', 'new_stock', 'created_at', 'created_by']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['product__name', 'reference']


# ==================== MAINTENANCE ADMIN ====================

@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'scheduled_date', 'scheduled_time', 'recurrence', 'status', 'created_at']
    list_filter = ['status', 'recurrence', 'scheduled_date', 'created_at']
    search_fields = ['title', 'assigned_to', 'description', 'notes']
    date_hierarchy = 'scheduled_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'assigned_to', 'status')
        }),
        ('Schedule Details', {
            'fields': ('scheduled_date', 'scheduled_time', 'recurrence')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaintenanceReport)
class MaintenanceReportAdmin(admin.ModelAdmin):
    list_display = ['category', 'description_preview', 'priority', 'status', 'reported_by', 'created_at']
    list_filter = ['category', 'priority', 'status', 'created_at']
    search_fields = ['category', 'description', 'resolution_notes']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    
    def description_preview(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_preview.short_description = 'Description'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('category', 'description', 'priority', 'status')
        }),
        ('Resolution Details', {
            'fields': ('resolution_notes', 'resolved_by', 'resolved_at')
        }),
        ('Metadata', {
            'fields': ('reported_by',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.reported_by:
            obj.reported_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_in_progress', 'mark_as_resolved', 'mark_as_closed']
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='In Progress')
        self.message_user(request, f'{updated} report(s) marked as In Progress.')
    mark_as_in_progress.short_description = 'Mark selected reports as In Progress'
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='Resolved', resolved_at=timezone.now(), resolved_by=request.user)
        self.message_user(request, f'{updated} report(s) marked as Resolved.')
    mark_as_resolved.short_description = 'Mark selected reports as Resolved'
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='Closed')
        self.message_user(request, f'{updated} report(s) marked as Closed.')
    mark_as_closed.short_description = 'Mark selected reports as Closed'