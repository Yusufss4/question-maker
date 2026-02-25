from django.urls import path
from core.views.login_views import login, voter_logout, AdminLoginView
from core.views.user_views import (
    survey_list,
    survey_detail,
    survey_vote,
    results_list,
    results_detail,
)
from core.views.admin_views import (
    admin_dashboard,
    admin_survey_list,
    admin_survey_create,
    admin_survey_edit,
    admin_survey_toggle_publish,
    admin_user_list,
    admin_user_create,
    admin_user_deactivate,
    admin_user_activate,
    admin_user_delete,
    admin_user_export,
    admin_vote_reset,
)

app_name = "core"

urlpatterns = [
    path("", login, name="login"),
    path("login/", login, name="login"),
    path("logout/", voter_logout, name="voter_logout"),
    path("admin-auth/login/", AdminLoginView.as_view(), name="admin_login"),
    # User area
    path("surveys/", survey_list, name="survey_list"),
    path("surveys/<int:pk>/", survey_detail, name="survey_detail"),
    path("surveys/<int:pk>/vote/", survey_vote, name="survey_vote"),
    path("results/", results_list, name="results_list"),
    path("results/<int:pk>/", results_detail, name="results_detail"),
    # Admin area
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/surveys/", admin_survey_list, name="admin_survey_list"),
    path("admin/surveys/new/", admin_survey_create, name="admin_survey_create"),
    path("admin/surveys/<int:pk>/edit/", admin_survey_edit, name="admin_survey_edit"),
    path("admin/surveys/<int:pk>/toggle-publish/", admin_survey_toggle_publish, name="admin_survey_toggle_publish"),
    path("admin/users/", admin_user_list, name="admin_user_list"),
    path("admin/users/new/", admin_user_create, name="admin_user_create"),
    path("admin/users/export/", admin_user_export, name="admin_user_export"),
    path("admin/users/<int:pk>/deactivate/", admin_user_deactivate, name="admin_user_deactivate"),
    path("admin/users/<int:pk>/activate/", admin_user_activate, name="admin_user_activate"),
    path("admin/users/<int:pk>/delete/", admin_user_delete, name="admin_user_delete"),
    path("admin/vote-reset/", admin_vote_reset, name="admin_vote_reset"),
]
