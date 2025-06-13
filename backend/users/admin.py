from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'username')
    search_fields = ('email', 'username', 'first_name', 'last_name') 