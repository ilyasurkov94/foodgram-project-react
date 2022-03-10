from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'email', 'username', 'first_name',
                    'last_name', 'password', 'role')
    list_editable = ('email', 'username', 'first_name',
                     'last_name', 'password', 'role')
    list_filter = ('username',)
    search_fields = ('pk', 'email', 'username', 'first_name', 'last_name')


admin.site.register(User, UserAdmin)
