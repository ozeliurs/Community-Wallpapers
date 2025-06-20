from django.contrib import admin
from .models import Image, ImageOfTheDay
from django.utils.html import format_html

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'upload_date', 'is_approved', 'image_preview')
    list_filter = ('is_approved', 'upload_date')
    actions = ['approve_images']
    
    def image_preview(self, obj):
        """Display a thumbnail preview in admin"""
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "No Image"
    
    image_preview.short_description = 'Preview'
    
    def approve_images(self, request, queryset):
        """Admin action to approve multiple images at once"""
        for image in queryset:
            image.approve()
        self.message_user(request, f"{queryset.count()} images were approved.")
    
    approve_images.short_description = "Approve selected images"

@admin.register(ImageOfTheDay)
class ImageOfTheDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'image', 'image_preview')
    list_filter = ('date',)
    date_hierarchy = 'date'
    
    def image_preview(self, obj):
        """Display a thumbnail preview in admin"""
        if obj.image.image:
            return format_html('<img src="{}" width="100" />', obj.image.image.url)
        return "No Image"
    
    image_preview.short_description = 'Preview'
