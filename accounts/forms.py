from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Order, Message, Product, Sale, Category, MaintenanceTask, MaintenanceReport
from django.core.validators import RegexValidator

# ==================== REGULAR FORMS ====================

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.address = self.cleaned_data['address']
            user.profile.role = 'customer'
            user.profile.save()
        
        return user

class StaffUserCreationForm(UserCreationForm):
    password2 = forms.CharField(widget=forms.HiddenInput, required=False)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    role = forms.ChoiceField(choices=[('staff', 'Staff'), ('rider', 'Rider')])
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound and self.data.get('password1') and not self.data.get('password2'):
            self.data = self.data.copy()
            self.data['password2'] = self.data['password1']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.role = self.cleaned_data['role']
            user.profile.save()
        
        return user

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'rider', 'total_amount', 'delivery_address', 'notes']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...', 'class': 'message-input'}),
        }

# ==================== POS FORMS ====================

class ProductForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = Product
        fields = ['name', 'category', 'water_type', 'container_type', 'product_type', 'sku', 'barcode',
                 'price', 'cost_price', 'stock_quantity', 'reorder_level',
                 'is_active', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        product_type = self.data.get('product_type') if self.is_bound else getattr(self.instance, 'product_type', None)
        if product_type == 'refill':
            self.fields['stock_quantity'].required = False
            self.fields['reorder_level'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('product_type') == 'refill':
            cleaned_data['stock_quantity'] = (
                getattr(self.instance, 'stock_quantity', None) or 0
            )
            cleaned_data['reorder_level'] = (
                getattr(self.instance, 'reorder_level', None) or 10
            )
            cleaned_data['is_active'] = (
                self.instance.is_active if self.instance.pk else True
            )
        return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'payment_method', 'discount', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = User.objects.filter(profile__role='customer', is_active=True)
        self.fields['customer'].required = False
        self.fields['customer'].widget.attrs.update({'class': 'form-control'})
        self.fields['payment_method'].widget.attrs.update({'class': 'form-control'})
        self.fields['discount'].widget.attrs.update({'class': 'form-control', 'min': '0'})

# ==================== MAINTENANCE FORMS ====================

class MaintenanceTaskForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ['title', 'description', 'scheduled_date', 'scheduled_time']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class MaintenanceReportForm(forms.ModelForm):
    class Meta:
        model = MaintenanceReport
        fields = ['category', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# ==================== EMAIL REGISTRATION FORM ====================

class EmailRegistrationForm(forms.Form):
    """Validate details for a new customer account."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    phone_number = forms.CharField(
        max_length=15,
        validators=[RegexValidator(r'^(?:\+[0-9]{9,14}|[0-9]{9,15})$', 'Enter a valid phone number using digits only.')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+63 XXX XXX XXXX'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Your delivery address'})
    )
    default_latitude = forms.DecimalField(
        required=False, max_digits=9, decimal_places=6, min_value=-90, max_value=90
    )
    default_longitude = forms.DecimalField(
        required=False, max_digits=9, decimal_places=6, min_value=-180, max_value=180
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists. Please login instead.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')

        latitude = cleaned_data.get('default_latitude')
        longitude = cleaned_data.get('default_longitude')
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError('Both location coordinates must be provided.')

        return cleaned_data
    
    def save_to_session(self, request):
        """Save registration data to session for later user creation"""
        request.session['pending_registration'] = {
            'username': self.cleaned_data['username'],
            'email': self.cleaned_data['email'],
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'phone_number': self.cleaned_data['phone_number'],
            'address': self.cleaned_data['address'],
            'default_latitude': (
                str(self.cleaned_data['default_latitude'])
                if self.cleaned_data.get('default_latitude') is not None else None
            ),
            'default_longitude': (
                str(self.cleaned_data['default_longitude'])
                if self.cleaned_data.get('default_longitude') is not None else None
            ),
            'password': self.cleaned_data['password1'],
        }


class GoogleProfileCompletionForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                r'^(?:\+[0-9]{9,14}|[0-9]{9,15})$',
                'Enter a valid phone number using digits only.',
            )
        ],
        widget=forms.TextInput(attrs={
            'autocomplete': 'tel',
            'placeholder': '+63 XXX XXX XXXX',
        }),
    )
    address = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'autocomplete': 'street-address',
            'placeholder': 'House/unit, street, barangay, city',
        }),
    )
    default_latitude = forms.DecimalField(
        required=True,
        max_digits=9,
        decimal_places=6,
        min_value=-90,
        max_value=90,
        widget=forms.HiddenInput(),
    )
    default_longitude = forms.DecimalField(
        required=True,
        max_digits=9,
        decimal_places=6,
        min_value=-180,
        max_value=180,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('default_latitude')
        longitude = cleaned_data.get('default_longitude')
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError('Both location coordinates must be provided.')
        return cleaned_data