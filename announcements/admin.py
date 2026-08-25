from django.contrib import admin
from .models import Category, Announcement, AnnouncementAttachment


class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'is_active', 'created_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'target_audience', 'is_published', 'published_at', 'created_by']
    list_filter = ['priority', 'target_audience', 'is_published', 'category']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AnnouncementAttachmentInline]
    ordering = ['-priority', '-created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
