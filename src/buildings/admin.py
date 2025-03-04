from buildings.models import Building

from django.contrib import admin


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "address"]
    search_fields = ["name", "address"]
    list_filter = ["name", "address"]
