from django.contrib import admin
from django.utils.html import format_html
from .models import Product

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'image_preview', 'created_at', 'updated_at')
    search_fields = ('name','sku_no')
    list_filter = ('created_at', 'updated_at')
    list_per_page = 20
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    
    image_preview.short_description = 'Image'
    
admin.site.register(Product, ProductAdmin)

