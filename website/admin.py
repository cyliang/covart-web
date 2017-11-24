from django.contrib import admin

from . import models

@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'identity', 'graduate_year')
    list_filter = ('graduate_date', 'identity')


@admin.register(models.MemberMeta)
class MemberMetaAdmin(admin.ModelAdmin):
    list_display = ('member', 'category', 'year', 'title')
    list_filter = ('member', 'category', 'year')
    search_fields = ('title', 'meta')


@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


class PublicationAuthorInlineAdmin(admin.TabularInline):
    model = models.PublicationAuthor
    extra = 2

@admin.register(models.Publication)
class PublicationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'authors')
    list_filter = ('paper_type', 'year', 'venue')
    list_display = ('title', 'authors', 'venue', 'year', 'paper_type')
    inlines = (PublicationAuthorInlineAdmin, )


@admin.register(models.InternalLink)
class LinkAdmin(admin.ModelAdmin):
    search_fields = ('title', 'help_text')
    list_display = ('title', 'help_text', 'update_time')
    list_filter = ('update_time',)
