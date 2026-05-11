from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("upload/", views.upload_resume, name="upload_resume"),
    path("analysis/<int:pk>/", views.analysis_dashboard, name="analysis_dashboard"),
    path("profile/", views.profile, name="profile"),
    path("api/analysis/<int:pk>/", views.analysis_detail_api, name="analysis_detail_api"),
    path("api/analysis/<int:pk>/coach/", views.resume_coach_api, name="resume_coach_api"),
    path("api/analyze-text/", views.analyze_text_api, name="analyze_text_api"),
    path("api/upload-analysis/", views.upload_analysis_api, name="upload_analysis_api"),
]
