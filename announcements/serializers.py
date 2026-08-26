from rest_framework import serializers
from .models import Category, Announcement, AnnouncementAttachment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'description', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class AnnouncementAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementAttachment
        fields = ['id', 'announcement', 'file', 'filename', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class AnnouncementSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    attachments = AnnouncementAttachmentSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'category', 'category_name',
            'priority', 'target_audience', 'is_published', 'published_at',
            'expires_at', 'created_by', 'created_by_name', 'attachments',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'category', 'category_name',
            'priority', 'target_audience', 'is_published',
            'published_at', 'expires_at', 'is_active', 'created_at'
        ]
