from django.urls import path, include



from . import views






urlpatterns = [

    path(
        'private-payment-proof/<path:path>',
        views.private_media,
        name='private_payment_proof',
    ),
    path(
        'private-media/<path:path>',
        views.private_media,
        name='private_media',
    ),

    # Authentication



    path('login/', views.login_view, name='login'),

    path('terms-of-service/', views.legal_policy, {'policy_type': 'terms'}, name='terms_of_service'),
    path('privacy-policy/', views.legal_policy, {'policy_type': 'privacy'}, name='privacy_policy'),
    path('contact/submit/', views.submit_contact_message, name='submit_contact_message'),



    path('logout/', views.logout_view, name='logout'),



    path('register/', views.register_view, name='register'),



    # User Profile (Google OAuth info)



    path('profile/', views.user_profile, name='user_profile'),



    path('api/profile/', views.social_profile_info, name='social_profile_api'),



    



    # Dashboards



    path('dashboard-redirect/', views.dashboard_redirect, name='dashboard_redirect'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/announcements/', views.admin_announcement_api, name='admin_announcement_api'),
    path('admin-dashboard/announcements/<int:announcement_id>/', views.admin_announcement_detail_api, name='admin_announcement_detail_api'),

    path('maintenance/', views.maintenance, name='maintenance'),

    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),



    path('rider/dashboard/', views.rider_dashboard, name='rider_dashboard'),



    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path(
        'customer-dashboard/complete-google-profile/',
        views.complete_google_profile,
        name='complete_google_profile',
    ),



    



    # User management



    path('manage-users/', views.manage_users, name='manage_users'),



    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),



    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),



    



    # Order management



    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('return-orders/', views.return_orders, name='return_orders'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('update-order-delivery-fee/', views.update_order_delivery_fee, name='update_order_delivery_fee'),
    path('get-order/<int:order_id>/', views.get_order_json, name='get_order_json'),  # API



    



    # Customer orders



    path('customer/order/', views.customer_order_page, name='customer_order'),



    path('customer/orders/', views.customer_orders, name='customer_orders'),
    path('customer/returns/', views.customer_returns, name='customer_returns'),
    path('customer/orders/<int:order_id>/return/', views.create_return_request, name='create_return_request'),
    path('return-requests/<int:return_request_id>/review/', views.review_return_request, name='review_return_request'),
    path('return-requests/<int:return_request_id>/assign-pickup/', views.assign_return_pickup, name='assign_return_pickup'),
    path('rider/return-pickups/<int:return_request_id>/update/', views.update_return_pickup_status, name='update_return_pickup_status'),
    path('return-requests/<int:return_request_id>/inspect/', views.inspect_return_request, name='inspect_return_request'),



    path('customer/place-order/', views.customer_place_order, name='customer_place_order'),



    path('customer/order-detail/<int:order_id>/', views.customer_order_detail, name='customer_order_detail'),



    path('customer/cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),



    



    # Customer profile


    path('account/profile/', views.account_profile, name='account_profile'),


    path('customer/profile/', views.customer_profile, name='customer_profile'),



    



    # Rider



    path('rider/accept-order/<int:order_id>/', views.rider_accept_order, name='rider_accept_order'),



    path('rider/delivery-history/', views.rider_delivery_history, name='rider_delivery_history'),



    path('rider/mark-out-for-delivery/<int:order_id>/', views.rider_mark_out_for_delivery, name='rider_mark_out_for_delivery'),



    path('rider/receive-order/<int:order_id>/', views.rider_receive_order, name='rider_receive_order'),



    path('rider/update-status/<int:order_id>/', views.rider_update_order_status, name='rider_update_order_status'),



    path('rider/mark-delivered/<int:order_id>/', views.rider_mark_delivered, name='rider_mark_delivered'),



 



    # ── NEW: Rider pushes its own GPS location to the server ──────



    path('rider/update-location/',



         views.update_rider_location,



         name='update_rider_location'),



 



    # ── NEW: Customer fetches the assigned rider's live location ──



    #   Called by customer_orders.html and customer_order_detail.html



    path('order/<int:order_id>/rider-location/',



         views.get_rider_location,



         name='get_rider_location'),



 



    # ── Existing rider mark-delivered (make sure this exists) ─────



    path('rider/mark-delivered/<int:order_id>/',

         views.rider_mark_delivered,

         name='rider_mark_delivered'),

    path('rider/order/<int:order_id>/message/',

         views.rider_order_message,

         name='rider_order_message'),







    # ── MESSAGING / COMMUNICATION ──────────────────────────────



    path('messages/', views.messaging_inbox, name='messaging_inbox'),



    path('messages/<int:conv_id>/', views.conversation_detail, name='conversation_detail'),



    path('messages/compose/', views.compose_message, name='compose_message'),



    path('messages/unread-count/', views.unread_message_count_api, name='unread_message_count_api'),
    path('orders/pending-count/', views.pending_order_count_api, name='pending_order_count_api'),
    path('rider/order-updates/', views.rider_order_updates_api, name='rider_order_updates_api'),
    path('live-updates/', views.live_updates_api, name='live_updates_api'),
    path('station-availability/', views.station_availability_api, name='station_availability_api'),
    path('settings/wifi/', views.wifi_configuration, name='wifi_configuration'),
    path('iot/wifi/<uuid:device_token>/', views.wifi_device_credentials, name='wifi_device_credentials'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('notifications/api/read/', views.notification_action_api, name='notifications_mark_all'),
    path('notifications/api/<int:notification_id>/', views.notification_action_api, name='notification_action'),
    path('contact-messages/', views.contact_messages_page, name='contact_messages'),



    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),



    # ── POS / SALES ───────────────────────────────────────────



    path('pos/', views.pos_dashboard, name='pos_dashboard'),



    path('pos/create-sale/', views.create_sale, name='create_sale'),



    path('pos/sales/', views.sale_list, name='sale_list'),



    path('pos/sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),



    path('pos/sales/<int:sale_id>/receipt/', views.receipt_view, name='receipt_view'),



    path('pos/sales/<int:sale_id>/void/', views.void_sale, name='void_sale'),







    # POS Products



    path('pos/products/', views.product_list, name='product_list'),



    path('pos/products/create/', views.product_create, name='product_create'),
    path('pos/products/<int:product_id>/delete/', views.product_delete, name='product_delete'),



    path('pos/products/<int:product_id>/edit/', views.product_edit, name='product_edit'),







    # POS Inventory



    path('pos/inventory/', views.inventory_list, name='inventory_list'),



    path('pos/inventory/<int:product_id>/adjust/', views.adjust_inventory, name='adjust_inventory'),







    # POS Reports



    path('pos/reports/sales/', views.sales_report, name='sales_report'),
    
    # Inventory Reports - ADD THIS LINE
    path('pos/reports/inventory/', views.inventory_reports, name='inventory_reports'),

    # Maintenance Reports
    path('pos/reports/maintenance/', views.maintenance_reports, name='maintenance_reports'),
    

    # Add these to urlpatterns

# Maintenance URLs
path('maintenance/', views.maintenance_view, name='maintenance'),
path('api/maintenance/tasks/', views.get_maintenance_tasks, name='get_maintenance_tasks'),
path('api/maintenance/reports/', views.get_maintenance_reports, name='get_maintenance_reports'),
path('api/maintenance/task/create/', views.create_maintenance_task, name='create_maintenance_task'),
path('api/maintenance/report/create/', views.create_maintenance_report, name='create_maintenance_report'),
path('api/maintenance/report/<int:report_id>/photos/', views.upload_maintenance_report_photos, name='upload_maintenance_report_photos'),
path('api/maintenance/task/<int:task_id>/delete/', views.delete_maintenance_task, name='delete_maintenance_task'),
path('api/maintenance/report/<int:report_id>/delete/', views.delete_maintenance_report, name='delete_maintenance_report'),
path('api/maintenance/task/<int:task_id>/status/', views.update_maintenance_task_status, name='update_task_status'),
path('api/maintenance/report/<int:report_id>/status/', views.update_maintenance_report_status, name='update_report_status'),

# Add these to urlpatterns
path('verify-email/', views.email_verification_view, name='email_verification'),
path('api/verify-email/', views.verify_email_otp, name='verify_email'),
path('api/resend-otp/', views.resend_verification_otp, name='resend_otp'),

]