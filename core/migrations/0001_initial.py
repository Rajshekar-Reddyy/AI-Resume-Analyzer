# Generated for the AI Resume Analyzer starter project.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Skill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("category", models.CharField(blank=True, max_length=80)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="JobDescription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("company", models.CharField(blank=True, max_length=160)),
                ("description", models.TextField()),
                ("extracted_keywords", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="job_descriptions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Resume",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_file", models.FileField(upload_to="resumes/%Y/%m/%d/")),
                ("extracted_text", models.TextField(blank=True)),
                ("extracted_skills", models.JSONField(blank=True, default=list)),
                ("education", models.JSONField(blank=True, default=list)),
                ("experience_years", models.DecimalField(decimal_places=1, default=0, max_digits=4)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resumes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ats_score", models.PositiveSmallIntegerField()),
                ("match_score", models.PositiveSmallIntegerField()),
                ("similarity_score", models.FloatField(default=0)),
                ("extracted_skills", models.JSONField(blank=True, default=list)),
                ("matched_skills", models.JSONField(blank=True, default=list)),
                ("missing_skills", models.JSONField(blank=True, default=list)),
                ("keyword_recommendations", models.JSONField(blank=True, default=list)),
                ("suggestions", models.JSONField(blank=True, default=list)),
                ("quality_checks", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "job_description",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to="core.jobdescription",
                    ),
                ),
                (
                    "resume",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to="core.resume",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
