from django.contrib import admin

from . import models

@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'identity', 'graduate_year')
    list_filter = ('graduate_date', 'identity')


@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


@admin.register(models.Publication)
class PublicationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
