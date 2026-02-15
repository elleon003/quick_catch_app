from django.db import models
from django.conf import settings
from django.utils import timezone

class AuthProvider(models.Model):
    PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google'),
        ('linkedin', 'LinkedIn'),
        ('magic_link', 'Magic Link'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auth_providers')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255, blank=True, null=True)
    provider_email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = [['user', 'provider'], ['provider', 'provider_user_id']]
        indexes = [
            models.Index(fields=['provider', 'provider_email']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_provider_display()}"
    
    def mark_used(self):
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])

class AuthLinkingToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Link token for {self.user.email} - {self.provider}"