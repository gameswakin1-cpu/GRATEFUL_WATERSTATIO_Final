import json
from contextlib import nullcontext
from io import BytesIO
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

from .adapters import CustomSocialAccountAdapter
from .decorators import customer_required
from .forms import (
    EmailRegistrationForm,
    GoogleProfileCompletionForm,
    SaleForm,
    StaffUserCreationForm,
)
from .middleware import NoStoreCacheMiddleware
from .storage import VercelPrivateBlobStorage
from .models import (
    Consumer,
    Order,
    ReturnRequest,
    ReturnRequestImage,
    UserProfile,
    create_user_profile,
    save_user_profile,
)
from . import views


class RoleRequiredTests(SimpleTestCase):
    def test_customer_route_creates_missing_profile(self):
        request = RequestFactory().get('/accounts/customer/order/')
        request.user = SimpleNamespace(is_authenticated=True)
        customer_profile = SimpleNamespace(role='customer')

        @customer_required
        def customer_view(request):
            return HttpResponse('ok')

        with patch.object(
            UserProfile.objects,
            'get_or_create',
            return_value=(customer_profile, True),
        ) as get_or_create:
            response = customer_view(request)

        self.assertEqual(response.status_code, 200)
        get_or_create.assert_called_once_with(
            user=request.user,
            defaults={'role': 'customer'},
        )


class VercelPrivateBlobStorageTests(SimpleTestCase):
    def test_order_payment_proof_uses_blob_storage(self):
        self.assertIsInstance(
            Order._meta.get_field('payment_proof').storage,
            VercelPrivateBlobStorage,
        )
        self.assertIsInstance(
            Order._meta.get_field('delivery_image').storage,
            VercelPrivateBlobStorage,
        )
        self.assertIsInstance(
            ReturnRequest._meta.get_field('evidence_image').storage,
            VercelPrivateBlobStorage,
        )
        self.assertIsInstance(
            ReturnRequestImage._meta.get_field('image').storage,
            VercelPrivateBlobStorage,
        )
        for model, field_name in (
            (views.ProductImage, 'image'),
            (views.AdminAnnouncementImage, 'image'),
            (views.MaintenanceReport, 'photo'),
            (views.MaintenanceReportPhoto, 'image'),
        ):
            self.assertIsInstance(
                model._meta.get_field(field_name).storage,
                VercelPrivateBlobStorage,
            )

    def test_save_uses_private_blob_storage_and_returns_blob_path(self):
        storage = VercelPrivateBlobStorage()
        blob_client = Mock()
        blob_client.put_blob.return_value.pathname = (
            'payment_proofs/proof-random.png'
        )
        uploaded_file = SimpleUploadedFile(
            'proof.png',
            b'proof-data',
            content_type='image/png',
        )

        with patch.object(storage, '_blob', return_value=blob_client):
            saved_name = storage._save('payment_proofs/proof.png', uploaded_file)

        self.assertEqual(saved_name, 'payment_proofs/proof-random.png')
        blob_client.put_blob.assert_called_once()
        args, kwargs = blob_client.put_blob.call_args
        self.assertEqual(args[0], 'payment_proofs/proof.png')
        self.assertEqual(b''.join(args[1]), b'proof-data')
        self.assertEqual(kwargs, {
            'access': 'private',
            'content_length': 10,
            'content_type': 'image/png',
            'add_random_suffix': True,
        })

    def test_payment_proof_view_requires_staff_access(self):
        request = RequestFactory().get(
            '/accounts/private-media/payment_proofs/proof.png'
        )
        request.user = SimpleNamespace(is_authenticated=False)

        response = views.private_media(
            request,
            'payment_proofs/proof.png',
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            '/accounts/login/?next=/accounts/private-media/payment_proofs/proof.png',
        )

    def test_staff_can_view_private_payment_proof(self):
        request = RequestFactory().get(
            '/accounts/private-media/payment_proofs/proof.png'
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        proof_content = BytesIO(b'proof-data')
        payment_proof = SimpleNamespace(open=Mock(return_value=proof_content))
        order = SimpleNamespace(payment_proof=payment_proof)
        queryset = Mock()
        queryset.first.return_value = order

        with patch.object(views.Order.objects, 'filter', return_value=queryset) as filter_orders:
            response = views.private_media(
                request,
                'payment_proofs/proof.png',
            )

        filter_orders.assert_called_once_with(
            payment_proof='payment_proofs/proof.png'
        )
        self.assertEqual(b''.join(response.streaming_content), b'proof-data')
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_customer_can_view_own_delivery_photo(self):
        request = RequestFactory().get('/accounts/private-media/delivery.png')
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_superuser=False,
            pk=12,
            profile=SimpleNamespace(role='customer'),
        )
        delivery_image = SimpleNamespace(
            name='delivery.png',
            open=Mock(return_value=BytesIO(b'delivery-data')),
        )
        order = SimpleNamespace(
            payment_proof=None,
            delivery_image=delivery_image,
            customer_id=12,
            rider_id=34,
        )
        no_match = Mock()
        no_match.first.return_value = None
        matching_order = Mock()
        matching_order.first.return_value = order

        with patch.object(
            views.Order.objects,
            'filter',
            side_effect=[no_match, matching_order],
        ):
            response = views.private_media(request, 'delivery.png')

        self.assertEqual(b''.join(response.streaming_content), b'delivery-data')

    def test_customer_can_view_evidence_for_own_return(self):
        request = RequestFactory().get(
            '/accounts/private-media/return_evidence/evidence.png'
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_superuser=False,
            pk=12,
            profile=SimpleNamespace(role='customer'),
        )
        evidence_image = SimpleNamespace(
            name='return_evidence/evidence.png',
            open=Mock(return_value=BytesIO(b'evidence-data')),
        )
        return_request = SimpleNamespace(
            evidence_image=evidence_image,
            order=SimpleNamespace(customer_id=12, rider_id=34),
            pickup_rider_id=None,
        )
        no_match = Mock()
        no_match.first.return_value = None
        matching_return = Mock()
        matching_return.first.return_value = return_request
        matching_return.select_related.return_value = matching_return

        with (
            patch.object(views.Order.objects, 'filter', return_value=no_match),
            patch.object(
                views.ReturnRequest.objects,
                'filter',
                return_value=matching_return,
            ),
        ):
            response = views.private_media(
                request,
                'return_evidence/evidence.png',
            )

        self.assertEqual(b''.join(response.streaming_content), b'evidence-data')

    def test_staff_can_view_maintenance_report_photo(self):
        request = RequestFactory().get(
            '/accounts/private-media/maintenance_reports/photo.jpg'
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_superuser=False,
            pk=12,
            profile=SimpleNamespace(role='admin'),
        )
        photo = SimpleNamespace(
            image=SimpleNamespace(
                open=Mock(return_value=BytesIO(b'maintenance-data')),
            ),
        )
        no_match = Mock()
        no_match.first.return_value = None
        no_match.select_related.return_value = no_match
        matching_photo = Mock()
        matching_photo.first.return_value = photo

        with (
            patch.object(views.Order.objects, 'filter', return_value=no_match),
            patch.object(
                views.ReturnRequest.objects,
                'filter',
                return_value=no_match,
            ),
            patch.object(
                views.ReturnRequestImage.objects,
                'filter',
                return_value=no_match,
            ),
            patch.object(
                views.ProductImage.objects,
                'filter',
                return_value=no_match,
            ),
            patch.object(
                views.AdminAnnouncementImage.objects,
                'filter',
                return_value=no_match,
            ),
            patch.object(
                views.MaintenanceReportPhoto.objects,
                'filter',
                return_value=matching_photo,
            ),
        ):
            response = views.private_media(
                request,
                'maintenance_reports/photo.jpg',
            )

        self.assertEqual(b''.join(response.streaming_content), b'maintenance-data')


class UserProfileFixtureSignalTests(SimpleTestCase):
    def test_raw_user_fixture_save_does_not_create_or_save_profile(self):
        user = SimpleNamespace(profile=Mock())
        with patch.object(UserProfile.objects, 'create') as create_profile:
            create_user_profile(sender=User, instance=user, created=True, raw=True)
            save_user_profile(sender=User, instance=user, raw=True)

        create_profile.assert_not_called()
        user.profile.save.assert_not_called()


class EmailRegistrationLocationTests(SimpleTestCase):
    def test_registration_coordinates_are_optional(self):
        form = EmailRegistrationForm()
        self.assertFalse(form.fields['default_latitude'].required)
        self.assertFalse(form.fields['default_longitude'].required)

    def test_registration_coordinate_fields_enforce_geographic_ranges(self):
        form = EmailRegistrationForm()

        with self.assertRaises(ValidationError):
            form.fields['default_latitude'].clean('91')
        with self.assertRaises(ValidationError):
            form.fields['default_longitude'].clean('-181')


class ImmediateCustomerRegistrationTests(SimpleTestCase):
    def test_registration_creates_customer_without_email_verification(self):
        registration_form = Mock()
        registration_form.is_valid.return_value = True
        registration_form.cleaned_data = {
            'username': 'newcustomer',
            'email': 'newcustomer@example.com',
            'first_name': 'New',
            'last_name': 'Customer',
            'phone_number': '09171234567',
            'address': '12 Main St, Las Piñas City',
            'default_latitude': Decimal('14.123456'),
            'default_longitude': Decimal('121.123456'),
            'password1': 'customer-password-123',
        }
        user = SimpleNamespace()
        profile = SimpleNamespace(save=Mock())
        request = RequestFactory().post(reverse('register'))
        request.user = SimpleNamespace(is_authenticated=False)

        with (
            patch.object(views, 'EmailRegistrationForm', return_value=registration_form),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.User.objects, 'create_user', return_value=user) as create_user,
            patch.object(
                views.UserProfile.objects, 'get_or_create', return_value=(profile, False)
            ),
            patch.object(views.Consumer.objects, 'get_or_create') as get_consumer,
            patch.object(views, 'send_verification_email') as send_email,
            patch.object(views, 'login') as login,
            patch.object(views.messages, 'success'),
        ):
            response = views.register_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('customer_dashboard'))
        self.assertIs(user.profile, profile)
        create_user.assert_called_once_with(
            username='newcustomer',
            email='newcustomer@example.com',
            password='customer-password-123',
            first_name='New',
            last_name='Customer',
        )
        self.assertEqual(profile.role, 'customer')
        self.assertEqual(profile.phone_number, '09171234567')
        self.assertEqual(profile.address, '12 Main St, Las Piñas City')
        self.assertEqual(profile.default_latitude, Decimal('14.123456'))
        self.assertEqual(profile.default_longitude, Decimal('121.123456'))
        profile.save.assert_called_once_with()
        get_consumer.assert_called_once_with(user=user)
        send_email.assert_not_called()
        login.assert_called_once_with(
            request, user, backend='django.contrib.auth.backends.ModelBackend'
        )


class QuickSaleFormTests(SimpleTestCase):
    def test_walk_in_sale_is_valid_without_a_customer(self):
        form = SaleForm(data={
            'customer': '',
            'payment_method': 'cash',
            'discount': '0',
            'notes': '',
        })

        self.assertTrue(form.is_valid(), form.errors)


class WifiConfigurationTests(SimpleTestCase):
    def render_configuration(self, config):
        request = RequestFactory().get(
            '/accounts/settings/wifi/',
            HTTP_HOST='127.0.0.1:8000',
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        queryset = Mock()
        queryset.first.return_value = config
        with (
            patch.object(views.WifiConfiguration.objects, 'order_by', return_value=queryset),
            patch.object(views, 'render') as render_template,
        ):
            views.wifi_configuration(request)
        return render_template.call_args[0][2]

    def post_configuration(self, config, password):
        request = RequestFactory().post(
            '/settings/wifi/',
            {'ssid': 'New Network', 'password': password},
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        queryset = Mock()
        queryset.first.return_value = config
        with (
            patch.object(views.WifiConfiguration.objects, 'order_by', return_value=queryset),
            patch.object(views.messages, 'success'),
            patch.object(views.messages, 'error'),
        ):
            response = views.wifi_configuration(request)
        return response

    def test_existing_configuration_can_change_network_and_password(self):
        configuration = SimpleNamespace(
            ssid='Old Network',
            password='old-password',
            save=Mock(),
        )

        response = self.post_configuration(configuration, 'new-password')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(configuration.ssid, 'New Network')
        self.assertEqual(configuration.password, 'new-password')
        configuration.save.assert_called_once_with()

    def test_blank_password_keeps_existing_password_while_changing_network(self):
        configuration = SimpleNamespace(
            ssid='Old Network',
            password='existing-password',
            save=Mock(),
        )

        response = self.post_configuration(configuration, '')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(configuration.ssid, 'New Network')
        self.assertEqual(configuration.password, 'existing-password')
        configuration.save.assert_called_once_with()

    @override_settings(WIFI_CREDENTIALS_BASE_URL='https://station.example')
    def test_device_endpoint_uses_configured_reachable_base_url(self):
        configuration = SimpleNamespace(
            device_token='00000000-0000-0000-0000-000000000001',
        )

        context = self.render_configuration(configuration)

        self.assertTrue(
            context['wifi_device_endpoint'].startswith(
                'https://station.example/accounts/iot/wifi/'
            )
        )
        self.assertEqual(context['wifi_device_endpoint_warning'], '')

    @override_settings(WIFI_CREDENTIALS_BASE_URL='')
    def test_localhost_device_endpoint_displays_reachability_warning(self):
        configuration = SimpleNamespace(
            device_token='00000000-0000-0000-0000-000000000001',
        )

        context = self.render_configuration(configuration)

        self.assertIn('cannot be reached by the ESP12E', context['wifi_device_endpoint_warning'])


class StaffUserCreationFormTests(SimpleTestCase):
    def test_form_omits_email_and_uses_password_as_confirmation(self):
        password = 'WaterStation!9482'
        form = StaffUserCreationForm(data={
            'username': 'new_staff_account',
            'first_name': 'New',
            'last_name': 'Staff',
            'phone_number': '09171234567',
            'role': 'staff',
            'password1': password,
        })

        self.assertNotIn('email', form.fields)
        self.assertTrue(form.fields['password2'].widget.is_hidden)
        self.assertEqual(form.data['password2'], password)


class MaintenanceStatusUpdateTests(SimpleTestCase):
    def setUp(self):
        self.staff = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )

    def test_task_status_update_saves_canonical_pending_status(self):
        task = SimpleNamespace(status='In Progress', save=Mock())
        request = RequestFactory().put(
            '/accounts/api/maintenance/task/1/status/',
            data=json.dumps({'status': 'Pending'}),
            content_type='application/json',
        )
        request.user = self.staff

        with patch.object(views, 'get_object_or_404', return_value=task):
            response = views.update_maintenance_task_status(request, task_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.status, 'Pending')
        task.save.assert_called_once()

    def test_task_status_update_rejects_unknown_status(self):
        task = SimpleNamespace(status='Pending', save=Mock())
        request = RequestFactory().put(
            '/accounts/api/maintenance/task/1/status/',
            data=json.dumps({'status': 'Unknown'}),
            content_type='application/json',
        )
        request.user = self.staff

        with patch.object(views, 'get_object_or_404', return_value=task):
            response = views.update_maintenance_task_status(request, task_id=1)

        self.assertEqual(response.status_code, 400)
        task.save.assert_not_called()


class OrderDeliveryFeeUpdateTests(SimpleTestCase):
    def setUp(self):
        self.staff = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        self.station_availability = SimpleNamespace(
            delivery_fee_up_to_2km=Decimal('20.00'),
            delivery_fee_up_to_3km=Decimal('30.00'),
            save=Mock(),
        )
        self.order = SimpleNamespace(
            delivery_lat=None,
            delivery_lng=None,
            delivery_address='Registered Address',
            subtotal=Decimal('100.00'),
            discount=Decimal('5.00'),
            delivery_fee=Decimal('20.00'),
            delivery_distance_km=Decimal('0.00'),
            delivery_area='Registered Address',
            delivery_fee_requires_approval=False,
            total_amount=Decimal('115.00'),
            updated_at=None,
        )
        self.orders = Mock()
        self.orders.iterator.return_value = iter([self.order])

    def post_update(self, payload):
        request = RequestFactory().post(
            '/accounts/update-order-delivery-fee/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        request.user = self.staff
        return request

    @staticmethod
    def valid_fee_rates():
        return {
            'up_to_2km': '21.50',
            'up_to_3km': '31.50',
        }

    def test_tier_rates_update_all_undelivered_orders_and_recalculate_totals(self):
        request = self.post_update(self.valid_fee_rates())
        with (
            patch.object(
                views.StationAvailability.objects,
                'get_or_create',
                return_value=(self.station_availability, False),
            ),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.Order.objects, 'exclude', return_value=self.orders) as undelivered_orders,
            patch.object(views.Order.objects, 'bulk_update') as bulk_update,
        ):
            response = views.update_order_delivery_fee(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'success': True,
            'fee_rates': {
                'up_to_2km': '21.50',
                'up_to_3km': '31.50',
            },
            'updated_orders': 1,
        })
        self.station_availability.save.assert_called_once_with(
            update_fields=[
                'delivery_fee_up_to_2km',
                'delivery_fee_up_to_3km',
                'updated_at',
            ],
        )
        undelivered_orders.assert_called_once_with(status='delivered')
        self.assertEqual(self.order.delivery_fee, Decimal('21.50'))
        self.assertEqual(self.order.total_amount, Decimal('116.50'))
        bulk_update.assert_called_once()

    def test_delivery_fee_update_rejects_invalid_amount(self):
        invalid_rates = self.valid_fee_rates()
        invalid_rates['up_to_2km'] = '-1.00'
        request = self.post_update(invalid_rates)

        with patch.object(views.StationAvailability.objects, 'get_or_create') as get_setting:
            response = views.update_order_delivery_fee(request)

        self.assertEqual(response.status_code, 400)
        get_setting.assert_not_called()

    def test_delivery_fee_update_rejects_more_than_two_decimal_places(self):
        invalid_rates = self.valid_fee_rates()
        invalid_rates['up_to_3km'] = '1.001'
        request = self.post_update(invalid_rates)

        with patch.object(views.StationAvailability.objects, 'get_or_create') as get_setting:
            response = views.update_order_delivery_fee(request)

        self.assertEqual(response.status_code, 400)
        get_setting.assert_not_called()


class MaintenanceTaskSchedulingTests(SimpleTestCase):
    def setUp(self):
        self.admin = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )

    def test_task_can_be_scheduled_without_a_time(self):
        scheduled_date = timezone.localdate() + timedelta(days=1)
        task = SimpleNamespace(id=18)
        request = RequestFactory().post(
            '/accounts/api/maintenance/task/create/',
            data=json.dumps({
                'title': 'Inspect water pump',
                'date': scheduled_date.isoformat(),
                'description': 'Check for leaks.',
            }),
            content_type='application/json',
        )
        request.user = self.admin

        with patch.object(
            views.MaintenanceTask.objects,
            'create',
            return_value=task,
        ) as create_task:
            response = views.create_maintenance_task(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            create_task.call_args.kwargs['scheduled_date'],
            scheduled_date,
        )
        self.assertIsNone(create_task.call_args.kwargs['scheduled_time'])


class MaintenanceReportCreateTests(SimpleTestCase):
    def setUp(self):
        self.admin = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )

    def create_test_image(self):
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='red').save(image_buffer, format='PNG')
        return SimpleUploadedFile(
            'maintenance-issue.png',
            image_buffer.getvalue(),
            content_type='image/png',
        )

    def test_report_saves_due_date_and_uploaded_photo(self):
        report = SimpleNamespace(id=45)
        request = RequestFactory().post(
            '/accounts/api/maintenance/report/create/',
            data={
                'category': 'Filter System',
                'description': 'Filter housing is cracked.',
                'priority': 'High',
                'due_date': timezone.localdate().isoformat(),
                'photo': self.create_test_image(),
            },
        )
        request.user = self.admin

        with patch.object(
            views.MaintenanceReport.objects,
            'create',
            return_value=report,
        ) as create_report:
            response = views.create_maintenance_report(request)

        self.assertEqual(response.status_code, 200)
        created_fields = create_report.call_args.kwargs
        self.assertEqual(
            created_fields['due_date'],
            timezone.localdate(),
        )
        self.assertEqual(created_fields['photo'].name, 'maintenance-issue.png')

    def test_report_requires_due_date(self):
        request = RequestFactory().post(
            '/accounts/api/maintenance/report/create/',
            data={'category': 'Filter System', 'priority': 'Medium'},
        )
        request.user = self.admin

        with patch.object(views.MaintenanceReport.objects, 'create') as create_report:
            response = views.create_maintenance_report(request)

        self.assertEqual(response.status_code, 400)
        create_report.assert_not_called()


class DeliveryFeeDistanceTests(SimpleTestCase):
    def test_customer_order_page_uses_default_rates_when_settings_table_is_unavailable(self):
        request = RequestFactory().get('/accounts/customer/order/')
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='customer'),
        )
        products = Mock()
        products.order_by.return_value = []

        with (
            patch.object(views.Product.objects, 'filter', return_value=products),
            patch.object(
                views.StationAvailability.objects,
                'get_or_create',
                side_effect=views.DatabaseError('settings table unavailable'),
            ),
            patch.object(views, 'render') as render_page,
        ):
            views.customer_order_page(request)

        context = render_page.call_args.args[2]
        self.assertEqual(context['delivery_fee_rates'], {
            'up_to_2km': Decimal('20.00'),
            'up_to_3km': Decimal('30.00'),
        })

    def test_customer_order_page_uses_manage_orders_fee_rates(self):
        station_availability = SimpleNamespace(
            delivery_fee_up_to_2km=Decimal('22.00'),
            delivery_fee_up_to_3km=Decimal('33.00'),
        )
        request = RequestFactory().get('/accounts/customer-order/')
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='customer'),
        )
        products = Mock()
        products.order_by.return_value = []

        with (
            patch.object(views.Product.objects, 'filter', return_value=products),
            patch.object(
                views.StationAvailability.objects,
                'get_or_create',
                return_value=(station_availability, False),
            ),
            patch.object(views, 'render') as render_page,
        ):
            views.customer_order_page(request)

        context = render_page.call_args.args[2]
        self.assertEqual(context['delivery_fee_rates'], {
            'up_to_2km': Decimal('22.00'),
            'up_to_3km': Decimal('33.00'),
        })
        self.assertEqual(context['delivery_base_fee'], Decimal('22.00'))

    def test_delivery_within_200_meters_is_free(self):
        fee, distance_km, _, requires_approval = views.calculate_delivery_fee(
            views.STATION_LAT + 0.00179,
            views.STATION_LNG,
        )

        self.assertEqual(fee, Decimal('0.00'))
        self.assertEqual(distance_km, Decimal('0.20'))
        self.assertFalse(requires_approval)

    def test_delivery_fee_uses_configured_two_and_three_kilometer_tiers(self):
        fee_rates = {
            'up_to_2km': Decimal('12.00'),
            'up_to_3km': Decimal('23.00'),
        }
        fee_1_5km, _, _, _ = views.calculate_delivery_fee(
            views.STATION_LAT + (1.5 / 111.2),
            views.STATION_LNG,
            fee_rates=fee_rates,
        )
        fee_2_5km, _, _, _ = views.calculate_delivery_fee(
            views.STATION_LAT + (2.5 / 111.2),
            views.STATION_LNG,
            fee_rates=fee_rates,
        )

        self.assertEqual(fee_1_5km, Decimal('12.00'))
        self.assertEqual(fee_2_5km, Decimal('23.00'))

    def test_delivery_beyond_three_kilometers_uses_three_kilometer_fee(self):
        fee_rates = {
            'up_to_2km': Decimal('12.00'),
            'up_to_3km': Decimal('23.00'),
        }
        fee, _, _, requires_approval = views.calculate_delivery_fee(
            views.STATION_LAT + (6 / 111.2),
            views.STATION_LNG,
            fee_rates=fee_rates,
        )

        self.assertEqual(fee, Decimal('23.00'))
        self.assertTrue(requires_approval)

    def test_delivery_beyond_200_meters_uses_existing_fee_tier(self):
        fee, distance_km, _, requires_approval = views.calculate_delivery_fee(
            views.STATION_LAT + 0.00181,
            views.STATION_LNG,
        )

        self.assertEqual(fee, Decimal('20.00'))
        self.assertEqual(distance_km, Decimal('0.20'))
        self.assertFalse(requires_approval)


class BuyTenGetOnePromotionTests(SimpleTestCase):
    def test_promotion_is_not_applied_before_eleven_items(self):
        products = [(SimpleNamespace(price=Decimal('15.00')), 10)]

        self.assertEqual(views.calculate_buy_ten_get_one_discount(products), Decimal('0.00'))

    def test_promotion_discounts_the_cheapest_unit_for_each_eleven_items(self):
        products = [
            (SimpleNamespace(price=Decimal('30.00')), 10),
            (SimpleNamespace(price=Decimal('15.00')), 1),
        ]

        self.assertEqual(views.calculate_buy_ten_get_one_discount(products), Decimal('15.00'))

    def test_promotion_repeats_for_each_additional_eleven_items(self):
        products = [(SimpleNamespace(price=Decimal('15.00')), 22)]

        self.assertEqual(views.calculate_buy_ten_get_one_discount(products), Decimal('30.00'))


class ReceiptEmbeddingTests(SimpleTestCase):
    def test_receipt_allows_framing_only_from_same_origin(self):
        request = RequestFactory().get('/accounts/pos/sales/95/receipt/?floating=1')
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        sale = SimpleNamespace(order_number=None)

        with (
            patch.object(views, 'get_object_or_404', return_value=sale),
            patch.object(views, 'render', return_value=HttpResponse('receipt')),
        ):
            response = views.receipt_view(request, 95)

        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')

    def test_account_profile_allows_same_origin_dashboard_modal(self):
        request = RequestFactory().get('/accounts/account/profile/?floating=1')
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        profile_response = HttpResponse('profile')

        with patch.object(views, 'customer_profile', return_value=profile_response):
            response = views.account_profile(request)

        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')

    def test_receipt_ajax_returns_data_for_customer_style_receipt(self):
        customer = SimpleNamespace(
            get_full_name=lambda: 'Ken Casares',
            username='kencasares',
        )
        item = SimpleNamespace(
            product=SimpleNamespace(name='Gallon Slim Container'),
            quantity=1,
            subtotal=Decimal('15.00'),
        )
        sale = SimpleNamespace(
            order_number=None,
            items=SimpleNamespace(all=lambda: [item]),
            receipt_number='REC-20261008-0001',
            get_status_display=lambda: 'Completed',
            discount=Decimal('0.00'),
            total_amount=Decimal('15.00'),
            customer=customer,
            get_payment_method_display=lambda: 'Cash',
            created_at=timezone.now(),
        )
        request = RequestFactory().get(
            '/accounts/pos/sales/95/receipt/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )

        with patch.object(views, 'get_object_or_404', return_value=sale):
            response = views.receipt_view(request, 95)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload['receipt_number'], 'REC-20261008-0001')
        self.assertEqual(payload['customer_name'], 'Ken Casares')
        self.assertEqual(payload['items'][0]['product_name'], 'Gallon Slim Container')
        self.assertEqual(payload['total_amount'], '15.00')
        self.assertIsNone(payload['delivered_at'])


class AuthenticationBrowserNavigationTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.authenticated_user = SimpleNamespace(is_authenticated=True)

    def test_authenticated_user_is_redirected_away_from_login_form(self):
        request = self.request_factory.get('/accounts/login/')
        request.user = self.authenticated_user

        response = views.login_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/accounts/dashboard-redirect/')

    def test_authenticated_user_is_redirected_away_from_registration_form(self):
        request = self.request_factory.get('/accounts/register/')
        request.user = self.authenticated_user

        response = views.register_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/accounts/dashboard-redirect/')

    def test_authenticated_user_is_redirected_away_from_home_page(self):
        request = self.request_factory.get('/')
        request.user = self.authenticated_user

        response = views.home(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/accounts/dashboard-redirect/')

    def test_responses_are_not_stored_by_the_browser(self):
        request = self.request_factory.get('/accounts/customer-dashboard/')
        request.user = self.authenticated_user
        middleware = NoStoreCacheMiddleware(lambda _: HttpResponse('account page'))

        response = middleware(request)

        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(response['Pragma'], 'no-cache')
        self.assertEqual(response['Expires'], '0')


class DashboardNotificationsApiTests(SimpleTestCase):
    def test_staff_dashboard_notifications_include_orders_stock_and_messages(self):
        user = SimpleNamespace(
            is_authenticated=True,
            pk=42,
            profile=SimpleNamespace(role='staff'),
        )
        request = RequestFactory().get('/accounts/notifications/api/')
        request.user = user
        unread_messages = Mock()
        unread_messages.exclude.return_value.count.return_value = 2
        low_stock_products = Mock()
        low_stock_products.count.return_value = 1
        active_orders = Mock()
        active_orders.count.return_value = 3

        with (
            patch.object(views.Notification.objects, 'filter', return_value=[]),
            patch.object(views.Message.objects, 'filter', return_value=unread_messages),
            patch.object(views.Product.objects, 'filter', return_value=low_stock_products),
            patch.object(views.Order.objects, 'exclude', return_value=active_orders),
        ):
            response = views.notifications_api(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(
            {item['id'] for item in payload['notifications']},
            {'unread-messages', 'low-stock', 'active-orders'},
        )
        self.assertEqual(payload['unread_count'], 1)

    def test_customer_notifications_only_include_orders_and_sliding_announcements(self):
        user = SimpleNamespace(
            is_authenticated=True,
            pk=43,
            profile=SimpleNamespace(role='customer'),
        )
        request = RequestFactory().get('/accounts/notifications/api/')
        request.user = user
        customer_orders = Mock()
        customer_orders.exclude.return_value.count.return_value = 1
        announcement = SimpleNamespace(
            id=8,
            headline='Weekend promo',
            description='Save on your next order.',
            created_at=timezone.now(),
            get_category_display=lambda: 'Promo / Discount',
        )

        with (
            patch.object(views.Notification.objects, 'filter', return_value=[]) as notification_filter,
            patch.object(views.Order.objects, 'filter', return_value=customer_orders),
            patch.object(views.AdminAnnouncementImage.objects, 'all', return_value=[announcement]),
            patch.object(views.Message.objects, 'filter') as message_filter,
        ):
            response = views.notifications_api(request)

        payload = json.loads(response.content)
        self.assertEqual(
            {item['category'] for item in payload['notifications']},
            {'orders', 'announcement'},
        )
        self.assertIn(
            'announcement-8',
            {item['id'] for item in payload['notifications']},
        )
        notification_filter.assert_called_once_with(
            recipient=user,
            is_archived=False,
            category__in=('orders', 'announcement'),
        )
        message_filter.assert_not_called()


class MarkAllNotificationsReadTests(SimpleTestCase):
    def test_mark_all_read_updates_notifications_and_incoming_messages(self):
        user = SimpleNamespace(is_authenticated=True, pk=44)
        request = RequestFactory().post(
            '/accounts/notifications/api/read/',
            data=json.dumps({'action': 'read'}),
            content_type='application/json',
        )
        request.user = user
        notifications = Mock()
        messages = Mock()
        messages.exclude.return_value = messages

        with (
            patch.object(views.Notification.objects, 'filter', return_value=notifications),
            patch.object(views.Message.objects, 'filter', return_value=messages),
        ):
            response = views.notification_action_api(request)

        self.assertEqual(response.status_code, 200)
        notifications.update.assert_called_once_with(is_read=True)
        messages.update.assert_called_once_with(is_read=True)


class ReturnRequestReviewTests(SimpleTestCase):
    def setUp(self):
        self.admin = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        self.return_request = SimpleNamespace(
            id=5,
            status='pending',
            order=SimpleNamespace(
                order_number='WS-1005',
                customer=SimpleNamespace(id=12),
            ),
            save=Mock(),
        )
        self.return_request.get_status_display = lambda: self.return_request.status

    def post_review(self, payload):
        request = RequestFactory().post(
            '/returns/5/review/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        request.user = self.admin
        return request

    def test_reject_requires_a_reason(self):
        with (
            patch.object(views.ReturnRequest.objects, 'select_related', return_value=Mock()),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.Notification.objects, 'create') as create_notification,
        ):
            response = views.review_return_request(self.post_review({'action': 'reject'}), 5)

        self.assertEqual(response.status_code, 400)
        self.return_request.save.assert_not_called()
        create_notification.assert_not_called()

    def test_rejection_note_is_saved_and_sent_to_the_customer(self):
        with (
            patch.object(views.ReturnRequest.objects, 'select_related', return_value=Mock()),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.Notification.objects, 'create') as create_notification,
        ):
            response = views.review_return_request(
                self.post_review({'action': 'reject', 'notes': 'The evidence does not show the issue.'}),
                5,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.return_request.status, 'rejected')
        self.assertEqual(self.return_request.review_notes, 'The evidence does not show the issue.')
        self.return_request.save.assert_called_once()
        self.assertIn(
            'The evidence does not show the issue.',
            create_notification.call_args.kwargs['description'],
        )

    def test_approval_requires_a_rider(self):
        with (
            patch.object(views.ReturnRequest.objects, 'select_related', return_value=Mock()),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
        ):
            response = views.review_return_request(
                self.post_review({'action': 'approve'}),
                5,
            )

        self.assertEqual(response.status_code, 400)
        self.return_request.save.assert_not_called()

    def test_approval_can_assign_a_rider_immediately(self):
        rider = SimpleNamespace(
            id=17,
            username='rider',
            get_full_name=lambda: 'Return Rider',
        )
        rider_query = Mock()
        rider_query.first.return_value = rider
        with (
            patch.object(views.ReturnRequest.objects, 'select_related', return_value=Mock()),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.User.objects, 'filter', return_value=rider_query) as filter_riders,
            patch.object(views.Notification.objects, 'create') as create_notification,
        ):
            response = views.review_return_request(
                self.post_review({'action': 'approve', 'rider_id': 17}),
                5,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.return_request.pickup_rider, rider)
        self.assertEqual(self.return_request.pickup_status, 'assigned')
        self.assertEqual(create_notification.call_count, 2)
        filter_riders.assert_called_once_with(
            id=17,
            profile__role='rider',
            is_active=True,
        )


class PartialReturnSubmissionTests(SimpleTestCase):
    def test_customer_cannot_return_more_than_the_purchased_quantity(self):
        order_item = SimpleNamespace(
            id=31,
            quantity=2,
            product=SimpleNamespace(name='Gallon Blue Water Container'),
        )
        order = SimpleNamespace(
            id=21,
            delivered_at=timezone.now(),
            updated_at=timezone.now(),
        )
        request = RequestFactory().post(
            '/accounts/customer/orders/21/return/',
            data={
                'items': json.dumps([{'order_item_id': 31, 'quantity': 3}]),
                'reason': 'damaged',
            },
        )
        request.user = SimpleNamespace(id=7, is_authenticated=True)
        order_item_query = Mock()
        order_item_query.select_related.return_value = [order_item]

        with (
            patch.object(views, 'get_object_or_404', return_value=order),
            patch.object(views.OrderItem.objects, 'filter', return_value=order_item_query),
            patch.object(views.ReturnRequest.objects, 'create') as create_return,
        ):
            response = views.create_return_request(request, order_id=21)

        self.assertEqual(response.status_code, 400)
        create_return.assert_not_called()

    def test_customer_can_submit_one_of_multiple_units_for_return(self):
        order_item = SimpleNamespace(
            id=31,
            quantity=2,
            product=SimpleNamespace(name='Gallon Blue Water Container'),
        )
        order = SimpleNamespace(
            id=21,
            delivered_at=timezone.now(),
            updated_at=timezone.now(),
        )
        return_request = SimpleNamespace(
            id=41,
            status='pending',
            get_status_display=lambda: 'Pending review',
        )
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1)).save(image_buffer, format='PNG')
        image_buffer.seek(0)
        request = RequestFactory().post(
            '/accounts/customer/orders/21/return/',
            data={
                'items': json.dumps([{'order_item_id': 31, 'quantity': 1}]),
                'reason': 'damaged',
                'details': 'One container is damaged.',
                'evidence_images': SimpleUploadedFile(
                    'damage.png',
                    image_buffer.read(),
                    content_type='image/png',
                ),
            },
        )
        request.user = SimpleNamespace(id=7, is_authenticated=True)
        order_item_query = Mock()
        order_item_query.select_related.return_value = [order_item]
        order_return_query = Mock()
        order_return_query.exists.return_value = False

        with (
            patch.object(views, 'get_object_or_404', return_value=order),
            patch.object(views.OrderItem.objects, 'filter', return_value=order_item_query),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.ReturnRequest.objects, 'filter', return_value=order_return_query),
            patch.object(views.ReturnRequest.objects, 'create', return_value=return_request),
            patch.object(views.ReturnRequestItem.objects, 'bulk_create') as create_return_items,
            patch.object(views.ReturnRequestImage.objects, 'create'),
            patch.object(views.User.objects, 'filter', return_value=[]),
            patch.object(views.Notification.objects, 'bulk_create'),
        ):
            response = views.create_return_request(request, order_id=21)

        self.assertEqual(response.status_code, 201)
        created_items = create_return_items.call_args.args[0]
        self.assertEqual(len(created_items), 1)
        self.assertEqual(created_items[0].order_item_id, order_item.id)
        self.assertEqual(created_items[0].quantity, 1)


class ReturnOrdersPageTests(SimpleTestCase):
    def test_staff_page_renders_return_request_list(self):
        request = RequestFactory().get(reverse('return_orders'))
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        return_queryset = Mock()
        return_queryset.select_related.return_value = return_queryset
        return_queryset.prefetch_related.return_value = return_queryset
        return_queryset.order_by.return_value = return_queryset
        return_queryset.filter.return_value = return_queryset
        return_page = SimpleNamespace(
            object_list=[],
            paginator=SimpleNamespace(num_pages=1),
        )
        paginator = Mock()
        paginator.get_page.return_value = return_page
        riders = Mock()
        riders.order_by.return_value = []

        with (
            patch.object(views.ReturnRequest.objects, 'select_related', return_value=return_queryset),
            patch.object(views.ReturnRequest.objects, 'count', return_value=0),
            patch.object(views.ReturnRequest.objects, 'filter', return_value=return_queryset),
            patch.object(views.User.objects, 'filter', return_value=riders),
            patch.object(views, 'Paginator', return_value=paginator),
            patch.object(views, 'render', return_value=HttpResponse()) as render,
        ):
            response = views.return_orders(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[1], 'accounts/return_orders.html')
        self.assertEqual(render.call_args.args[2]['return_requests'], [])


class ReturnPickupWorkflowTests(SimpleTestCase):
    def setUp(self):
        self.customer = SimpleNamespace(id=12)
        self.rider = SimpleNamespace(
            id=17,
            username='rider',
            is_authenticated=True,
            profile=SimpleNamespace(role='rider'),
            get_full_name=lambda: 'Return Rider',
        )
        self.admin = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        self.return_request = SimpleNamespace(
            id=5,
            status='approved',
            pickup_status='assigned',
            pickup_rider=self.rider,
            order=SimpleNamespace(order_number='WS-1005', customer=self.customer),
            save=Mock(),
        )
        self.return_request.get_pickup_status_display = (
            lambda: self.return_request.pickup_status
        )

    def test_staff_can_assign_an_approved_return_to_active_rider(self):
        self.return_request.pickup_status = 'awaiting_assignment'
        request = RequestFactory().post(
            '/returns/5/assign-pickup/',
            data=json.dumps({'rider_id': self.rider.id}),
            content_type='application/json',
        )
        request.user = self.admin
        rider_queryset = Mock(first=Mock(return_value=self.rider))
        return_queryset = Mock()
        return_queryset.select_related.return_value = return_queryset
        notification_model = Mock()

        with (
            patch.object(views.User.objects, 'filter', return_value=rider_queryset),
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=return_queryset),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views, 'Notification', notification_model),
        ):
            response = views.assign_return_pickup(request, return_request_id=5)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.return_request.pickup_status, 'assigned')
        self.assertIs(self.return_request.pickup_rider, self.rider)
        self.return_request.save.assert_called_once()
        self.assertEqual(notification_model.objects.bulk_create.call_count, 1)
        self.assertEqual(
            len(notification_model.objects.bulk_create.call_args.args[0]),
            2,
        )

    def post_update(self, payload):
        request = RequestFactory().post(
            '/rider/return-pickups/5/update/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        request.user = self.rider
        return request

    def test_rider_can_mark_assigned_return_as_picked_up(self):
        queryset = Mock()
        queryset.select_related.return_value = queryset
        with (
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=queryset),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.Notification.objects, 'create') as create_notification,
        ):
            response = views.update_return_pickup_status(
                self.post_update({'action': 'picked_up'}),
                return_request_id=5,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.return_request.pickup_status, 'picked_up')
        self.assertIsNotNone(self.return_request.picked_up_at)
        self.return_request.save.assert_called_once()
        self.assertEqual(create_notification.call_args.kwargs['recipient'], self.customer)

    def test_rider_can_mark_payment_returned_after_pickup(self):
        self.return_request.pickup_status = 'picked_up'
        queryset = Mock()
        queryset.select_related.return_value = queryset
        with (
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=queryset),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.Notification.objects, 'create') as create_notification,
        ):
            response = views.update_return_pickup_status(
                self.post_update({'action': 'payment_returned'}),
                return_request_id=5,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.return_request.pickup_status, 'payment_returned')
        self.assertIsNotNone(self.return_request.payment_returned_at)
        self.return_request.save.assert_called_once()
        self.assertEqual(
            create_notification.call_args.kwargs['recipient'],
            self.customer,
        )

    def test_rider_can_mark_item_returned_after_payment_is_returned(self):
        self.return_request.pickup_status = 'payment_returned'
        queryset = Mock()
        queryset.select_related.return_value = queryset
        with (
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=queryset),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.Notification.objects, 'create'),
            patch.object(views.Notification.objects, 'bulk_create'),
            patch.object(views.User.objects, 'filter', return_value=[]),
        ):
            response = views.update_return_pickup_status(
                self.post_update({'action': 'received'}),
                return_request_id=5,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.return_request.pickup_status, 'received')
        self.assertIsNotNone(self.return_request.received_at)

    def test_rider_cannot_mark_return_received_before_payment_is_returned(self):
        self.return_request.pickup_status = 'picked_up'
        queryset = Mock()
        queryset.select_related.return_value = queryset
        with (
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=queryset),
            patch.object(views, 'get_object_or_404', return_value=self.return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
        ):
            response = views.update_return_pickup_status(
                self.post_update({'action': 'received'}),
                return_request_id=5,
            )

        self.assertEqual(response.status_code, 409)
        self.return_request.save.assert_not_called()


class ReturnInspectionTests(SimpleTestCase):
    def test_return_sales_adjustment_estimate_allocates_order_discount(self):
        order_item = SimpleNamespace(
            quantity=2,
            unit_price=Decimal('50.00'),
            subtotal=Decimal('100.00'),
        )
        return_item = SimpleNamespace(quantity=1, order_item=order_item)
        return_request = SimpleNamespace(
            order=SimpleNamespace(
                subtotal=Decimal('300.00'),
                discount=Decimal('30.00'),
            ),
        )

        amount = views._calculate_return_sales_adjustment(return_request, return_item)

        self.assertEqual(amount, Decimal('45.00'))

    def test_return_inspection_records_sales_adjustment_and_restock(self):
        order_item = SimpleNamespace(
            id=31,
            quantity=2,
            unit_price=Decimal('30.00'),
            subtotal=Decimal('60.00'),
            product_id=5,
            product=SimpleNamespace(name='Gallon Blue Water Container', product_type='gallon'),
        )
        return_item = SimpleNamespace(
            id=41,
            quantity=1,
            order_item=order_item,
            save=Mock(),
        )
        return_request = SimpleNamespace(
            id=51,
            status='approved',
            pickup_status='received',
            inspected_at=None,
            order=SimpleNamespace(
                order_number='WS-501',
                subtotal=Decimal('60.00'),
                discount=Decimal('0.00'),
                customer=SimpleNamespace(id=12),
            ),
            save=Mock(),
        )
        product = SimpleNamespace(
            id=5,
            name='Gallon Blue Water Container',
            stock_quantity=4,
            save=Mock(),
        )
        sale_item = SimpleNamespace(
            returned_quantity=0,
            returned_amount=Decimal('0.00'),
            save=Mock(),
        )
        sale = SimpleNamespace(returned_amount=Decimal('0.00'), save=Mock())
        request = RequestFactory().post(
            '/returns/51/inspect/',
            data=json.dumps({
                'items': [{'id': 41, 'restockable_quantity': 1}],
            }),
            content_type='application/json',
        )
        request.user = SimpleNamespace(
            id=9,
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        return_query = Mock()
        return_query.select_related.return_value = return_query
        item_query = Mock()
        item_query.filter.return_value.select_related.return_value = [return_item]
        product_query = Mock()
        product_query.get.return_value = product
        sale_item_query = Mock()
        sale_item_query.first.return_value = sale_item
        sale_query = Mock()
        sale_query.first.return_value = sale

        with (
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=return_query),
            patch.object(views.ReturnRequestItem.objects, 'select_for_update', return_value=item_query),
            patch.object(views, 'get_object_or_404', return_value=return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.SaleItem.objects, 'filter', return_value=sale_item_query),
            patch.object(views.Product.objects, 'select_for_update', return_value=product_query),
            patch.object(views.InventoryTransaction.objects, 'create') as create_inventory_transaction,
            patch.object(views.Sale.objects, 'filter', return_value=sale_query),
            patch.object(views.Notification.objects, 'create'),
        ):
            response = views.inspect_return_request(request, return_request_id=51)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_item.restockable_quantity, 1)
        self.assertEqual(return_item.sales_adjustment, Decimal('30.00'))
        self.assertEqual(sale_item.returned_quantity, 1)
        self.assertEqual(sale_item.returned_amount, Decimal('30.00'))
        self.assertEqual(sale.returned_amount, Decimal('30.00'))
        self.assertEqual(product.stock_quantity, 5)
        create_inventory_transaction.assert_called_once()
        self.assertEqual(json.loads(response.content)['restocked_quantity'], 1)

    def test_refill_return_records_adjustment_without_restock_input_or_stock_change(self):
        order_item = SimpleNamespace(
            id=32,
            quantity=2,
            unit_price=Decimal('4.00'),
            subtotal=Decimal('8.00'),
            product_id=7,
            product=SimpleNamespace(name='Water Refill', product_type='refill'),
        )
        return_item = SimpleNamespace(
            id=42,
            quantity=1,
            order_item=order_item,
            save=Mock(),
        )
        return_request = SimpleNamespace(
            id=52,
            status='approved',
            pickup_status='received',
            inspected_at=None,
            order=SimpleNamespace(
                order_number='WS-502',
                subtotal=Decimal('8.00'),
                discount=Decimal('0.00'),
                customer=SimpleNamespace(id=13),
            ),
            save=Mock(),
        )
        sale_item = SimpleNamespace(
            returned_quantity=0,
            returned_amount=Decimal('0.00'),
            save=Mock(),
        )
        sale = SimpleNamespace(returned_amount=Decimal('0.00'), save=Mock())
        request = RequestFactory().post(
            '/returns/52/inspect/',
            data=json.dumps({'items': []}),
            content_type='application/json',
        )
        request.user = SimpleNamespace(
            id=9,
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        return_query = Mock()
        return_query.select_related.return_value = return_query
        item_query = Mock()
        item_query.filter.return_value.select_related.return_value = [return_item]
        sale_item_query = Mock()
        sale_item_query.first.return_value = sale_item
        sale_query = Mock()
        sale_query.first.return_value = sale

        with (
            patch.object(views.ReturnRequest.objects, 'select_for_update', return_value=return_query),
            patch.object(views.ReturnRequestItem.objects, 'select_for_update', return_value=item_query),
            patch.object(views, 'get_object_or_404', return_value=return_request),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
            patch.object(views.SaleItem.objects, 'filter', return_value=sale_item_query),
            patch.object(views.Product.objects, 'select_for_update') as select_product,
            patch.object(views.InventoryTransaction.objects, 'create') as create_inventory_transaction,
            patch.object(views.Sale.objects, 'filter', return_value=sale_query),
            patch.object(views.Notification.objects, 'create'),
        ):
            response = views.inspect_return_request(request, return_request_id=52)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_item.restockable_quantity, 0)
        self.assertEqual(return_item.sales_adjustment, Decimal('4.00'))
        self.assertEqual(sale_item.returned_quantity, 1)
        self.assertEqual(sale_item.returned_amount, Decimal('4.00'))
        self.assertEqual(sale.returned_amount, Decimal('4.00'))
        select_product.assert_not_called()
        create_inventory_transaction.assert_not_called()
        self.assertEqual(json.loads(response.content)['restocked_quantity'], 0)


class LiveUpdatesReturnRequestTests(SimpleTestCase):
    def test_admin_live_updates_include_latest_return_request_token(self):
        updated_at = timezone.now()
        request = RequestFactory().get('/live-updates/')
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        empty_queryset = Mock(first=Mock(return_value=None))
        empty_count = Mock(count=Mock(return_value=0))
        notification_queryset = Mock(count=Mock(return_value=0))
        station = SimpleNamespace(
            is_open=True,
            delivery_fee_up_to_2km=Decimal('50.00'),
            delivery_fee_up_to_3km=Decimal('75.00'),
        )
        return_request_values = Mock(
            first=Mock(return_value={
                'id': 42,
                'updated_at': updated_at,
                'pickup_status': 'payment_returned',
            })
        )

        with (
            patch.object(views.Order.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.Order.objects, 'exclude', return_value=empty_count),
            patch.object(views.Product.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.Product.objects, 'filter', return_value=empty_count),
            patch.object(views.Sale.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.UserProfile.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.MaintenanceTask.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.MaintenanceReport.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.ReturnRequest.objects, 'order_by', return_value=Mock(values=Mock(return_value=return_request_values))),
            patch.object(views.StationAvailability.objects, 'get_or_create', return_value=(station, False)),
            patch.object(views.Message.objects, 'filter', return_value=Mock(exclude=Mock(return_value=empty_count))),
            patch.object(views.Notification.objects, 'filter', return_value=notification_queryset),
        ):
            response = views.live_updates_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)['return_requests'],
            {
                'latest_updated_at': updated_at.isoformat(),
                'latest_id': 42,
                'latest_pickup_status': 'payment_returned',
            },
        )

    def test_customer_live_updates_include_latest_return_pickup_status(self):
        updated_at = timezone.now()
        request = RequestFactory().get('/live-updates/')
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='customer'),
        )
        empty_queryset = Mock(first=Mock(return_value=None))
        empty_count = Mock(count=Mock(return_value=0))
        notification_queryset = Mock(count=Mock(return_value=0))
        station = SimpleNamespace(
            is_open=True,
            delivery_fee_up_to_2km=Decimal('50.00'),
            delivery_fee_up_to_3km=Decimal('75.00'),
        )
        latest_return = {
            'id': 42,
            'updated_at': updated_at,
            'pickup_status': 'payment_returned',
        }
        returns_queryset = Mock()
        returns_queryset.count.return_value = 1
        returns_queryset.order_by.return_value.values.return_value.first.return_value = latest_return
        orders_queryset = Mock()
        orders_queryset.exclude.return_value = empty_count
        order_list_queryset = Mock()
        order_list_queryset.order_by.return_value = []

        with (
            patch.object(views.Order.objects, 'order_by', return_value=empty_queryset),
            patch.object(
                views.Order.objects,
                'filter',
                side_effect=[orders_queryset, order_list_queryset],
            ),
            patch.object(views.Product.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.Product.objects, 'filter', return_value=empty_count),
            patch.object(views.Sale.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.UserProfile.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.MaintenanceTask.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.MaintenanceReport.objects, 'order_by', return_value=empty_queryset),
            patch.object(views.ReturnRequest.objects, 'filter', return_value=returns_queryset),
            patch.object(views.StationAvailability.objects, 'get_or_create', return_value=(station, False)),
            patch.object(views.Message.objects, 'filter', return_value=Mock(exclude=Mock(return_value=empty_count))),
            patch.object(views.Notification.objects, 'filter', return_value=notification_queryset),
        ):
            response = views.live_updates_api(request)

        self.assertEqual(response.status_code, 200)
        customer_returns = json.loads(response.content)['customer_returns']
        self.assertEqual(customer_returns['latest_pickup_status'], 'payment_returned')
        self.assertEqual(customer_returns['latest_id'], 42)


class RiderOnTheWayStatusTests(SimpleTestCase):
    def setUp(self):
        self.rider = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='rider'),
        )
        self.order = SimpleNamespace(
            status='send-to-rider',
            save=Mock(),
            get_status_display=Mock(return_value='Out for Delivery'),
        )

    def test_rider_can_mark_assigned_order_on_the_way(self):
        request = RequestFactory().post('/accounts/rider/mark-out-for-delivery/1/')
        request.user = self.rider

        with patch.object(views, 'get_object_or_404', return_value=self.order) as get_order:
            response = views.rider_mark_out_for_delivery(request, order_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'success': True,
            'status': 'out_for_delivery',
            'status_display': 'On the Way',
        })
        self.assertEqual(self.order.status, 'out_for_delivery')
        self.order.save.assert_called_once()
        get_order.assert_called_once_with(
            views.Order,
            id=1,
            rider=self.rider,
            status__in=['pending', 'processing', 'send-to-rider', 'rider_accepted'],
        )


class RiderDashboardStatsTests(SimpleTestCase):
    def test_dashboard_passes_all_three_daily_stats_to_template(self):
        rider = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='rider'),
        )
        request = RequestFactory().get('/accounts/rider-dashboard/')
        request.user = rider

        assigned_orders = Mock()
        assigned_orders.select_related.return_value = assigned_orders
        assigned_orders.prefetch_related.return_value = assigned_orders
        assigned_orders.order_by.return_value = assigned_orders
        assigned_orders.filter.return_value.count.side_effect = [2, 1, 3]

        completed_today = Mock()
        completed_today.count.return_value = 4
        earnings_today = Mock()
        earnings_today.aggregate.return_value = {'total_amount__sum': Decimal('425.50')}
        return_pickups = Mock()
        return_pickups.select_related.return_value = return_pickups
        return_pickups.order_by.return_value = return_pickups

        with (
            patch.object(
                views.Order.objects,
                'filter',
                side_effect=[assigned_orders, completed_today, earnings_today],
            ),
            patch.object(views.ReturnRequest.objects, 'filter', return_value=return_pickups),
            patch.object(views, 'render') as render,
        ):
            views.rider_dashboard(request)

        context = render.call_args.args[2]
        self.assertEqual(context['out_for_delivery_count'], 3)
        self.assertEqual(context['completed_count'], 4)
        self.assertEqual(context['today_earnings'], Decimal('425.50'))


class CustomerProfileMonthlyStatsTests(SimpleTestCase):
    def test_profile_shows_lifetime_totals_and_monthly_comparison(self):
        user = SimpleNamespace(
            is_authenticated=True,
            first_name='Ken',
            date_joined=timezone.now(),
            profile=SimpleNamespace(role='customer'),
        )
        request = RequestFactory().get('/accounts/profile/')
        request.user = user

        delivered_orders = Mock()
        this_month_orders = Mock()
        previous_month_orders = Mock()
        delivered_orders.filter.side_effect = [this_month_orders, previous_month_orders]
        delivered_orders.count.return_value = 12
        delivered_orders.aggregate.return_value = {'total_amount__sum': Decimal('820.00')}
        this_month_orders.count.return_value = 4
        previous_month_orders.count.return_value = 2
        this_month_orders.aggregate.return_value = {'total_amount__sum': Decimal('140.00')}
        previous_month_orders.aggregate.return_value = {'total_amount__sum': Decimal('125.00')}

        with (
            patch.object(views.Order.objects, 'filter', return_value=delivered_orders),
            patch.object(views, 'render') as render,
        ):
            views.customer_profile(request)

        context = render.call_args.args[2]
        self.assertTrue(context['show_customer_stats'])
        self.assertEqual(context['total_orders'], 12)
        self.assertEqual(context['total_spent'], '₱820.00')
        self.assertEqual(context['order_trend_text'], '+2 this month vs last month')
        self.assertEqual(context['spending_trend_text'], '+12.0% this month vs last month')

    def test_staff_profile_hides_customer_stats(self):
        user = SimpleNamespace(
            is_authenticated=True,
            first_name='Staff',
            profile=SimpleNamespace(role='staff'),
        )
        request = RequestFactory().get('/accounts/account/profile/?floating=1')
        request.user = user

        with (
            patch.object(views.Order.objects, 'filter') as order_filter,
            patch.object(views, 'render') as render,
        ):
            response = views.account_profile(request)

        self.assertIsNotNone(
            render.call_args,
            f'Profile request redirected to {getattr(response, "url", None)}',
        )
        context = render.call_args.args[2]
        self.assertFalse(context['show_customer_stats'])
        self.assertEqual(context['profile_route'], 'account_profile')
        self.assertTrue(context['floating_profile'])
        self.assertNotIn('total_orders', context)
        self.assertNotIn('total_spent', context)
        order_filter.assert_not_called()


class CustomerGcashOrderStatusTests(SimpleTestCase):
    def test_unconfirmed_gcash_order_is_displayed_as_awaiting_payment(self):
        order = Order(status='awaiting_payment')

        self.assertEqual(order.get_status_display(), 'Awaiting Payment')

    def test_staff_can_confirm_gcash_payment_to_enable_order_processing(self):
        request = RequestFactory().post(
            '/accounts/update-order-status/1/',
            data=json.dumps({'status': 'pending'}),
            content_type='application/json',
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )
        order = SimpleNamespace(
            status='awaiting_payment',
            payment_method='gcash',
            order_number='ORD-1000',
            save=Mock(),
            get_status_display=Mock(return_value='Pending'),
        )

        with patch.object(views, 'get_object_or_404', return_value=order):
            response = views.update_order_status(request, order_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['status'], 'pending')
        self.assertEqual(order.status, 'pending')
        order.save.assert_called_once()

    def test_unconfirmed_gcash_order_cannot_skip_payment_confirmation(self):
        request = RequestFactory().post(
            '/accounts/update-order-status/1/',
            data=json.dumps({'status': 'processing'}),
            content_type='application/json',
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        order = SimpleNamespace(
            status='awaiting_payment',
            payment_method='gcash',
            order_number='ORD-1000',
            save=Mock(),
        )

        with patch.object(views, 'get_object_or_404', return_value=order):
            response = views.update_order_status(request, order_id=1)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)['success'])
        self.assertEqual(order.status, 'awaiting_payment')
        order.save.assert_not_called()

    def test_staff_can_reselect_choose_rider_for_an_order_waiting_for_assignment(self):
        request = RequestFactory().post(
            '/accounts/update-order-status/1/',
            data=json.dumps({'status': 'choose_rider'}),
            content_type='application/json',
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        order = SimpleNamespace(
            status='choose_rider',
            payment_method='cod',
            order_number='ORD-1000',
            save=Mock(),
            get_status_display=Mock(return_value='Choose Rider'),
        )

        with patch.object(views, 'get_object_or_404', return_value=order):
            response = views.update_order_status(request, order_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['success'])
        self.assertEqual(order.status, 'choose_rider')
        order.save.assert_called_once()

    def test_staff_cannot_choose_rider_before_processing(self):
        request = RequestFactory().post(
            '/accounts/update-order-status/1/',
            data=json.dumps({'status': 'choose_rider'}),
            content_type='application/json',
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='staff'),
        )
        order = SimpleNamespace(
            status='pending',
            payment_method='cod',
            order_number='ORD-1000',
            save=Mock(),
        )

        with patch.object(views, 'get_object_or_404', return_value=order):
            response = views.update_order_status(request, order_id=1)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)['success'])
        order.save.assert_not_called()


class OnTheWayRiderAssignmentTests(SimpleTestCase):
    def test_staff_cannot_reassign_rider_after_order_is_on_the_way(self):
        current_rider_id = 7
        order = SimpleNamespace(
            status='out_for_delivery',
            rider_id=current_rider_id,
            payment_method='cod',
            save=Mock(),
        )
        request = RequestFactory().post(
            '/accounts/update-order-status/1/',
            data={
                'status': 'out_for_delivery',
                'rider_id': '12',
            },
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )

        with (
            patch.object(views, 'get_object_or_404', return_value=order),
            patch.object(views.messages, 'error'),
        ):
            response = views.update_order_status(request, order_id=1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(order.rider_id, current_rider_id)
        order.save.assert_not_called()


class OrderNumberGenerationTests(SimpleTestCase):
    def test_new_numbers_skip_sales_left_by_deleted_orders(self):
        order_queryset = MagicMock()
        order_queryset.values_list.return_value = ['ORD-1000', 'ORD-1002']
        sale_queryset = MagicMock()
        sale_queryset.values_list.return_value = ['ORD-1001']

        with (
            patch.object(views.Order.objects, 'all', return_value=order_queryset),
            patch.object(views.Sale.objects, 'exclude', return_value=sale_queryset),
        ):
            order_number = views._next_order_number()

        self.assertEqual(order_number, 'ORD-1003')


class ReportPeriodDefaultTests(SimpleTestCase):
    def test_daily_period_defaults_to_selected_day(self):
        end_date = date(2026, 9, 30)

        self.assertEqual(
            views._report_period_default_start('daily', end_date),
            end_date,
        )

    def test_weekly_period_defaults_to_monday_of_current_week(self):
        self.assertEqual(
            views._report_period_default_start('weekly', date(2026, 9, 30)),
            date(2026, 9, 28),
        )

    def test_monthly_period_defaults_to_first_day_of_current_month(self):
        self.assertEqual(
            views._report_period_default_start('monthly', date(2026, 9, 30)),
            date(2026, 9, 1),
        )


class VerificationEmailSendingTests(SimpleTestCase):
    @override_settings(
        EMAIL_HOST_USER='sender@gmail.com',
        EMAIL_HOST_PASSWORD='test-app-password',
        DEFAULT_FROM_EMAIL='sender@gmail.com',
    )
    @patch('django.core.mail.send_mail', return_value=1)
    def test_verification_email_uses_configured_sender(self, send_mail):
        sent = views.send_verification_email('customer@example.com', '123456')

        self.assertTrue(sent)
        self.assertEqual(send_mail.call_args.args[2], 'sender@gmail.com')
        self.assertEqual(send_mail.call_args.args[3], ['customer@example.com'])
        self.assertIn('123456', send_mail.call_args.args[1])

    @override_settings(EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='')
    @patch('django.core.mail.send_mail')
    def test_verification_email_fails_clearly_without_smtp_credentials(self, send_mail):
        self.assertFalse(
            views.send_verification_email('customer@example.com', '123456')
        )
        send_mail.assert_not_called()


class CustomSocialAccountAdapterTests(SimpleTestCase):
    def test_google_signup_uses_auto_signup_flow(self):
        sociallogin = SimpleNamespace(account=SimpleNamespace(provider='google'))

        self.assertTrue(
            CustomSocialAccountAdapter().is_auto_signup_allowed(
                RequestFactory().get('/accounts/social/google/login/callback/'),
                sociallogin,
            )
        )
    def test_google_profile_completion_requires_phone_address_and_paired_coordinates(self):
        form = GoogleProfileCompletionForm(data={
            'phone_number': '09171234567',
            'address': 'Unit 4, Brgy. Talon Uno, Las Piñas City',
            'default_latitude': '14.123456',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('default_longitude', form.errors)

    def test_google_profile_completion_requires_confirmed_location_coordinates(self):
        form = GoogleProfileCompletionForm(data={
            'phone_number': '09171234567',
            'address': 'Unit 4, Brgy. Talon Uno, Las Piñas City',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('default_latitude', form.errors)
        self.assertIn('default_longitude', form.errors)

    def test_google_signup_sets_dashboard_profile_completion_flag(self):
        user = SimpleNamespace(pk=42)
        profile = SimpleNamespace(role='', save=Mock())
        request = RequestFactory().post('/accounts/social/google/login/callback/')
        request.session = {}
        sociallogin = SimpleNamespace(account=SimpleNamespace(provider='google'))

        with (
            patch(
                'accounts.adapters.DefaultSocialAccountAdapter.save_user',
                return_value=user,
            ),
            patch.object(
                UserProfile.objects, 'get_or_create', return_value=(profile, False)
            ),
            patch.object(Consumer.objects, 'get_or_create'),
        ):
            CustomSocialAccountAdapter().save_user(request, sociallogin)

        self.assertEqual(request.session['google_profile_completion_user_id'], 42)
        self.assertIs(user.profile, profile)

    def test_profile_completion_endpoint_persists_contact_and_location(self):
        request = RequestFactory().post(
            '/accounts/customer-dashboard/complete-google-profile/',
            {
                'phone_number': '09171234567',
                'address': 'Unit 4, Brgy. Talon Uno, Las Piñas City',
                'default_latitude': '14.123456',
                'default_longitude': '121.123456',
            },
        )
        request.user = SimpleNamespace(pk=42, is_authenticated=True)
        request.session = {'google_profile_completion_user_id': 42}
        profile = SimpleNamespace(save=Mock())

        with (
            patch.object(
                UserProfile.objects, 'get_or_create', return_value=(profile, False)
            ),
            patch.object(Consumer.objects, 'get_or_create'),
        ):
            response = views.complete_google_profile(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'success': True})
        self.assertEqual(profile.phone_number, '09171234567')
        self.assertEqual(profile.address, 'Unit 4, Brgy. Talon Uno, Las Piñas City')
        self.assertEqual(profile.default_latitude, Decimal('14.123456'))
        self.assertEqual(profile.default_longitude, Decimal('121.123456'))
        profile.save.assert_called_once_with(update_fields=[
            'phone_number',
            'address',
            'default_latitude',
            'default_longitude',
        ])
        self.assertNotIn('google_profile_completion_user_id', request.session)

    def test_profile_completion_endpoint_rejects_another_session(self):
        request = RequestFactory().post(
            '/accounts/customer-dashboard/complete-google-profile/',
            {
                'phone_number': '09171234567',
                'address': 'Unit 4, Brgy. Talon Uno, Las Piñas City',
            },
        )
        request.user = SimpleNamespace(pk=42, is_authenticated=True)
        request.session = {'google_profile_completion_user_id': 7}

        response = views.complete_google_profile(request)

        self.assertEqual(response.status_code, 403)

    def test_profile_completion_allows_incomplete_google_profile_without_session_marker(self):
        request = RequestFactory().post(
            '/accounts/customer-dashboard/complete-google-profile/',
            {
                'phone_number': '09171234567',
                'address': 'Unit 4, Brgy. Talon Uno, Las Piñas City',
                'default_latitude': '14.123456',
                'default_longitude': '121.123456',
            },
        )
        request.user = SimpleNamespace(pk=42, is_authenticated=True)
        request.session = {}
        profile = SimpleNamespace(phone_number='', address='', save=Mock())
        social_accounts = Mock()
        social_accounts.exists.return_value = True

        with (
            patch.object(UserProfile.objects, 'filter') as profile_filter,
            patch(
                'allauth.socialaccount.models.SocialAccount.objects.filter',
                return_value=social_accounts,
            ) as social_filter,
            patch.object(
                UserProfile.objects, 'get_or_create', return_value=(profile, False)
            ),
            patch.object(Consumer.objects, 'get_or_create'),
        ):
            profile_filter.return_value.first.return_value = profile
            response = views.complete_google_profile(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'success': True})
        social_filter.assert_called_once_with(user_id=42, provider='google')

    def test_profile_completion_without_session_rejects_non_google_user(self):
        request = RequestFactory().post(
            '/accounts/customer-dashboard/complete-google-profile/',
            {
                'phone_number': '09171234567',
                'address': 'Unit 4, Brgy. Talon Uno, Las Piñas City',
                'default_latitude': '14.123456',
                'default_longitude': '121.123456',
            },
        )
        request.user = SimpleNamespace(pk=42, is_authenticated=True)
        request.session = {}
        profile = SimpleNamespace(phone_number='', address='')
        social_accounts = Mock()
        social_accounts.exists.return_value = False

        with (
            patch.object(UserProfile.objects, 'filter') as profile_filter,
            patch(
                'allauth.socialaccount.models.SocialAccount.objects.filter',
                return_value=social_accounts,
            ),
        ):
            profile_filter.return_value.first.return_value = profile
            response = views.complete_google_profile(request)

        self.assertEqual(response.status_code, 403)

    def test_duplicate_email_shows_actionable_error_instead_of_crashing(self):
        duplicate_users = [User(pk=1), User(pk=2)]
        queryset = MagicMock()
        queryset.order_by.return_value.__getitem__.return_value = duplicate_users
        sociallogin = SimpleNamespace(
            is_existing=False,
            email_addresses=[SimpleNamespace(email='customer@example.com')],
            state={'process': 'signup'},
        )
        request = RequestFactory().get('/accounts/social/google/login/callback/')
        response = HttpResponse()

        with (
            patch.object(User.objects, 'filter', return_value=queryset) as filter_users,
            patch('django.contrib.messages.error') as add_message,
            patch('django.shortcuts.render', return_value=response) as render,
        ):
            with self.assertRaises(ImmediateHttpResponse) as raised:
                CustomSocialAccountAdapter().pre_social_login(request, sociallogin)

        filter_users.assert_called_once_with(email__iexact='customer@example.com')
        add_message.assert_called_once()
        render.assert_called_once()
        self.assertEqual(render.call_args.args[1], 'accounts/register.html')
        self.assertIs(raised.exception.response, response)

    @override_settings(
        ALLOWED_HOSTS=['water.example.com'],
        USE_X_FORWARDED_HOST=True,
        SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
    )
    def test_google_callback_uses_forwarded_https_hostname(self):
        request = RequestFactory().get(
            '/',
            HTTP_HOST='127.0.0.1:8000',
            HTTP_X_FORWARDED_HOST='water.example.com',
            HTTP_X_FORWARDED_PROTO='https',
        )

        callback_url = GoogleOAuth2Adapter(request).get_callback_url(request, None)

        self.assertEqual(
            callback_url,
            'https://water.example.com/accounts/social/google/login/callback/',
        )


class AdminAnnouncementApiTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.admin = SimpleNamespace(
            is_authenticated=True,
            profile=SimpleNamespace(role='admin'),
        )

    def test_text_announcement_can_be_created_without_an_image(self):
        request = self.request_factory.post(
            '/accounts/admin-dashboard/announcements/',
            {
                'category': 'promo',
                'headline': 'Weekend discount',
                'description': 'Save on your next refill.',
            },
        )
        request.user = self.admin
        announcement = SimpleNamespace(
            id=12,
            image=None,
            category='promo',
            headline='Weekend discount',
            description='Save on your next refill.',
            get_category_display=Mock(return_value='Promo / Discount'),
        )
        customer = User(pk=33)

        with (
            patch.object(
                views.AdminAnnouncementImage.objects,
                'create',
                return_value=announcement,
            ) as create_announcement,
            patch.object(views.User.objects, 'filter', return_value=[customer]),
            patch.object(views.Notification.objects, 'bulk_create') as create_notifications,
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
        ):
            response = views.admin_announcement_api(request)

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['headline'], 'Weekend discount')
        self.assertEqual(response_data['url'], '')
        create_announcement.assert_called_once_with(
            image=None,
            category='promo',
            headline='Weekend discount',
            description='Save on your next refill.',
        )
        create_notifications.assert_called_once()
        created_notification = create_notifications.call_args.args[0][0]
        self.assertEqual(created_notification.category, 'announcement')
        self.assertEqual(created_notification.recipient, customer)
        self.assertEqual(created_notification.title, 'Weekend discount')
        self.assertEqual(created_notification.target_url, '/accounts/customer-dashboard/#customer-announcement-12')

    def test_headline_is_optional(self):
        request = self.request_factory.post(
            '/accounts/admin-dashboard/announcements/',
            {
                'category': 'important',
            },
        )
        request.user = self.admin
        announcement = SimpleNamespace(
            id=13,
            image=None,
            category='important',
            headline='',
            description='',
            get_category_display=Mock(return_value='Important Announcement'),
        )

        with (
            patch.object(
                views.AdminAnnouncementImage.objects,
                'create',
                return_value=announcement,
            ) as create_announcement,
            patch.object(views.User.objects, 'filter', return_value=[]),
            patch.object(views.Notification.objects, 'bulk_create'),
            patch.object(views.transaction, 'atomic', return_value=nullcontext()),
        ):
            response = views.admin_announcement_api(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content)['headline'], '')
        create_announcement.assert_called_once_with(
            image=None,
            category='important',
            headline='',
            description='',
        )
