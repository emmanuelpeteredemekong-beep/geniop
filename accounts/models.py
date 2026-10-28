from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Store(models.Model):
    """Professional Store / Account model for Geniop"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='store_profile',
        verbose_name='Linked User'
    )
    
    store_name = models.CharField(
        max_length=200,
        verbose_name='Store Name',
        help_text='Official registered store name'
    )
    
    owner_name = models.CharField(
        max_length=200,
        verbose_name='Owner Full Name'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in format: '+999999999'. Up to 15 digits."
    )
    
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name='Phone Number'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='Store Email'
    )
    
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Street Address'
    )
    
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Verified',
        help_text='Is this store verified by admin?'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'

    def __str__(self):
        return f"{self.store_name} - {self.owner_name}"

    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state}".strip(', ')
