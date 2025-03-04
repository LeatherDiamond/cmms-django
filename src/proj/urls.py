from buildings.views import (
    BuildingCreateView,
    BuildingDeleteView,
    BuildingListView,
    BuildingUpdateView,
)

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from homepage import views as homepage_views

from tasks.views import (
    TaskCreateView,
    TaskDeleteView,
    TaskEmployeeStatusUpdateView,
    TaskLeaveComment,
    TaskListView,
    TaskManagerStatusUpdateView,
    TaskUpdateView,
    serve_attachment,
)

from users import views as users_views


urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", homepage_views.IndexView.as_view(), name="index"),
        path("accounts/login/", users_views.LoginView.as_view(), name="login"),
        path("accounts/logout/", users_views.LogoutView.as_view(), name="logout"),
        path(
            "accounts/password_change/",
            users_views.CmmstPasswordChangeView.as_view(),
            name="password_change",
        ),
        path(
            "accounts/password_change/done/",
            users_views.CmmstPasswordChangeDoneView.as_view(),
            name="password_change_done",
        ),
        path(
            "accounts/password_change/first_login/",
            users_views.FirstLoginPasswordChangeView.as_view(),
            name="first_login_password_change",
        ),
        path(
            "accounts/password_reset/",
            users_views.PasswordResetView.as_view(),
            name="password_reset",
        ),
        path(
            "accounts/password_reset/done/",
            auth_views.PasswordResetDoneView.as_view(),
            name="password_reset_done",
        ),
        path(
            "accounts/reset/<uidb64>/<token>/",
            auth_views.PasswordResetConfirmView.as_view(),
            name="password_reset_confirm",
        ),
        path(
            "accounts/reset/done/",
            auth_views.PasswordResetCompleteView.as_view(),
            name="password_reset_complete",
        ),
        path("task/list/", TaskListView.as_view(), name="task_list"),
        path("task/create/", TaskCreateView.as_view(), name="task_create"),
        path("task/<int:pk>/update/", TaskUpdateView.as_view(), name="task_update"),
        path(
            "task/<int:pk>/status/<str:status>/",
            TaskManagerStatusUpdateView.as_view(),
            name="task_manager_status_update",
        ),
        path(
            "task/<int:pk>/empl_status/<str:status>/",
            TaskEmployeeStatusUpdateView.as_view(),
            name="task_employee_status_update",
        ),
        path("task/<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
        path(
            "task/<int:pk>/comment/",
            TaskLeaveComment.as_view(),
            name="task_leave_comment",
        ),
        path("building/list/", BuildingListView.as_view(), name="building_list"),
        path("building/create/", BuildingCreateView.as_view(), name="building_create"),
        path(
            "building/<int:pk>/update/",
            BuildingUpdateView.as_view(),
            name="building_update",
        ),
        path(
            "building/<int:pk>/delete/",
            BuildingDeleteView.as_view(),
            name="building_delete",
        ),
        path("media/<path:file_path>/", serve_attachment, name="serve_attachment"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
