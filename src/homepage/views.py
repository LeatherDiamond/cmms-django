from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from tasks.models import Task


class IndexView(LoginRequiredMixin, View):
    """
    Main page view.
    """

    def get(self, request):
        user = request.user

        if user.is_manager:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(assigned_person=user)

        total_tasks = tasks.count()
        open_tasks = tasks.filter(status_field__isnull=True).count()
        closed_tasks = tasks.filter(status_field="accepted").count()
        overdue_tasks = tasks.filter(
            deadline__lt=timezone.now(), status_field__isnull=True
        ).count()

        status_translation = {
            "failure": "Awaria",
            "planned": "Planowane",
            "high": "Wysoki",
            "medium": "Średni",
            "low": "Niski",
        }

        category_stats = [
            {
                "category": status_translation.get(item["category"], item["category"]),
                "count": item["count"],
            }
            for item in tasks.values("category").annotate(count=Count("id"))
        ]

        priority_stats = [
            {
                "priority": status_translation.get(item["priority"], item["priority"]),
                "count": item["count"],
            }
            for item in tasks.values("priority").annotate(count=Count("id"))
        ]

        avg_closure_time = None
        if user.is_manager:
            avg_closure_time = (
                Task.objects.filter(status_field="accepted")
                .annotate(
                    closure_time=ExpressionWrapper(
                        F("closed_at") - F("created_at"), output_field=DurationField()
                    )
                )
                .aggregate(avg_closure=Avg("closure_time"))["avg_closure"]
            )

            if avg_closure_time:
                total_seconds = avg_closure_time.total_seconds()
                days = int(total_seconds // 86400)
                hours = int((total_seconds % 86400) // 3600)
                minutes = int((total_seconds % 3600) // 60)
                avg_closure_time = f"{days} d. {hours} g. {minutes} min."

        recent_tasks = tasks.order_by("-created_at")[:5]

        context = {
            "user": user,
            "total_tasks": total_tasks,
            "open_tasks": open_tasks,
            "closed_tasks": closed_tasks,
            "overdue_tasks": overdue_tasks,
            "category_stats": category_stats,
            "priority_stats": priority_stats,
            "avg_closure_time": avg_closure_time,
            "recent_tasks": recent_tasks,
        }

        return render(request, "homepage/index.html", context)
