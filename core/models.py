from django.conf import settings
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobDescription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_descriptions",
    )
    title = models.CharField(max_length=160)
    company = models.CharField(max_length=160, blank=True)
    description = models.TextField()
    extracted_keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        company = f" at {self.company}" if self.company else ""
        return f"{self.title}{company}"


class Resume(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    original_file = models.FileField(upload_to="resumes/%Y/%m/%d/")
    extracted_text = models.TextField(blank=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.username} resume #{self.pk}"


class AnalysisResult(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analysis_results",
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="analysis_results",
    )
    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.CASCADE,
        related_name="analysis_results",
    )
    ats_score = models.PositiveSmallIntegerField()
    match_score = models.PositiveSmallIntegerField()
    similarity_score = models.FloatField(default=0)
    extracted_skills = models.JSONField(default=list, blank=True)
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    keyword_recommendations = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    quality_checks = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.resume} vs {self.job_description} ({self.ats_score}%)"
