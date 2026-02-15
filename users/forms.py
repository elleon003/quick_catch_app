from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser
from .turnstile import verify_turnstile, is_turnstile_enabled

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    cf_turnstile_response = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate Turnstile if enabled
        if is_turnstile_enabled():
            turnstile_response = cleaned_data.get('cf_turnstile_response')
            if not turnstile_response:
                raise forms.ValidationError('Please complete the CAPTCHA verification.')
            
            # Get user's IP address
            remote_ip = None
            if self.request:
                x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    remote_ip = x_forwarded_for.split(',')[0]
                else:
                    remote_ip = self.request.META.get('REMOTE_ADDR')
            
            if not verify_turnstile(turnstile_response, remote_ip):
                raise forms.ValidationError('CAPTCHA verification failed. Please try again.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'autofocus': True}),
        label='Email'
    )
    cf_turnstile_response = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field and replace with email
        self.fields['username'].widget.attrs.update({'placeholder': 'Email'})

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('username')  # Django form still uses 'username' internally
        password = cleaned_data.get('password')

        # Validate Turnstile if enabled
        if is_turnstile_enabled():
            turnstile_response = cleaned_data.get('cf_turnstile_response')
            if not turnstile_response:
                raise forms.ValidationError('Please complete the CAPTCHA verification.')
            
            # Get user's IP address
            remote_ip = None
            if self.request:
                x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    remote_ip = x_forwarded_for.split(',')[0]
                else:
                    remote_ip = self.request.META.get('REMOTE_ADDR')
            
            if not verify_turnstile(turnstile_response, remote_ip):
                raise forms.ValidationError('CAPTCHA verification failed. Please try again.')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,  # Pass email as username to authenticate
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Please enter a correct email and password.",
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return cleaned_data
