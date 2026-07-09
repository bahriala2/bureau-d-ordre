from django.contrib import admin

from .models import Service

admin.site.site_header = "Bureau d'ordre & Achats"
admin.site.site_title = "Administration"
admin.site.index_title = "Gestion administrative"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "actif")
    search_fields = ("nom", "code")
    list_filter = ("actif",)
