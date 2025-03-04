from buildings.forms import BuildingForm
from buildings.models import Building

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from users.models import AuditEntry


class BuildingListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Building
    permission_required = "buildings.view_building"
    template_name = "buildings/building_list.html"
    context_object_name = "buildings"
    paginate_by = 10

    def get_queryset(self):
        return Building.objects.order_by("name")


class BuildingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Building
    permission_required = "buildings.add_building"
    template_name = "buildings/building_create.html"
    form_class = BuildingForm
    success_url = reverse_lazy("building_list")

    def form_valid(self, form):
        try:
            building = form.save()
            AuditEntry.log_action(
                AuditEntry.BUILDING_CREATED,
                self.request,
                f"Budynek '{building.name}' został utworzony.",
            )
            messages.success(self.request, "Budynek utworzony pomyślnie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Budynek utworzony pomyślnie."}
                )
            return super().form_valid(form)
        except Exception as e:
            AuditEntry.log_action(
                AuditEntry.BUILDING_CREATION_FAILED,
                self.request,
                f"Błąd podczas tworzenia budynku: {str(e)}",
            )
            messages.error(self.request, "Wystąpił błąd. Spróbuj ponownie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": f"Błąd: {str(e)}"})
            raise

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Nieprawidłowe dane.",
                    "errors": form.errors,
                }
            )
        return super().form_invalid(form)


class BuildingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Building
    permission_required = "buildings.change_building"
    template_name = "buildings/building_update.html"
    form_class = BuildingForm
    success_url = reverse_lazy("building_list")

    def form_valid(self, form):
        try:
            building = form.save()
            AuditEntry.log_action(
                AuditEntry.BUILDING_UPDATED,
                self.request,
                f"Budynek '{building.name}' został zaktualizowany.",
            )
            messages.success(self.request, "Budynek zaktualizowany pomyślnie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Budynek zaktualizowany pomyślnie."}
                )
            return super().form_valid(form)
        except Exception as e:
            AuditEntry.log_action(
                AuditEntry.BUILDING_UPDATE_FAILED,
                self.request,
                f"Błąd podczas aktualizacji budynku: {str(e)}",
            )
            messages.error(self.request, "Wystąpił błąd. Spróbuj ponownie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": f"Błąd: {str(e)}"})
            raise

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Nieprawidłowe dane.",
                    "errors": form.errors,
                }
            )
        return super().form_invalid(form)


class BuildingDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "buildings.delete_building"

    def post(self, request, *args, **kwargs):
        building = get_object_or_404(Building, pk=kwargs.get("pk"))
        try:
            building.delete()
            AuditEntry.log_action(
                AuditEntry.BUILDING_DELETED,
                self.request,
                f"Budynek '{building.name}' został usunięty.",
            )
            messages.success(request, "Budynek usunięty pomyślnie.")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Budynek usunięty pomyślnie."},
                    status=200,
                )
            return redirect("building_list")
        except Exception as e:
            AuditEntry.log_action(
                AuditEntry.BUILDING_DELETE_FAILED,
                self.request,
                f"Bląd podczas usuwania budynku: {str(e)}",
            )
            messages.error(request, "Wystąpił błąd. Spróbuj ponownie.")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": f"Bląd: {str(e)}"}, status=400
                )
            return redirect("building_list")
