from django.contrib import admin

from .models import Member

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'identity', 'graduate_year')
    list_filter = ('graduate_date', 'identity')
