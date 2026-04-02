from django.contrib import admin

from lab.models import DipTest


@admin.register(DipTest)
class DipTestAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status")
    readonly_fields = ("created_at",)
    search_fields = ("id", "status")
