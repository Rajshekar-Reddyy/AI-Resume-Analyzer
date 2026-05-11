from django.contrib import admin

from .models import AnalysisResult, JobDescription, Resume, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name", "category")


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "company", "description", "user__username")


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("user", "experience_years", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("user__username", "extracted_text")


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("user", "job_description", "ats_score", "match_score", "created_at")
    list_filter = ("created_at", "ats_score", "match_score")
    search_fields = ("user__username", "job_description__title")
