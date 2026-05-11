import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileForm, RegisterForm, ResumeAnalysisForm
from .models import AnalysisResult, JobDescription, Resume
from .services.extractors import TextExtractionError, extract_text_from_upload
from .services.resume_coach import answer_resume_question, build_resume_review
from .services.scoring import analyze_resume


def home(request):
    recent_result = None
    if request.user.is_authenticated:
        recent_result = (
            AnalysisResult.objects.filter(user=request.user)
            .select_related("job_description")
            .first()
        )
    return render(request, "core/index.html", {"recent_result": recent_result})


def register(request):
    if request.user.is_authenticated:
        return redirect("upload_resume")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. You can analyze your first resume now.")
            return redirect("upload_resume")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def upload_resume(request):
    if request.method == "POST":
        form = ResumeAnalysisForm(request.POST, request.FILES)
        if form.is_valid():
            result = _create_analysis_from_form(request, form)
            if isinstance(result, AnalysisResult):
                messages.success(request, "Resume analyzed successfully.")
                return redirect("analysis_dashboard", pk=result.pk)
    else:
        form = ResumeAnalysisForm()

    return render(request, "core/upload.html", {"form": form})


@login_required
def analysis_dashboard(request, pk):
    result = get_object_or_404(
        AnalysisResult.objects.select_related("resume", "job_description"),
        pk=pk,
        user=request.user,
    )
    chart_payload = {
        "labels": ["Matched skills", "Missing skills"],
        "values": [len(result.matched_skills), len(result.missing_skills)],
    }
    quality_payload = {
        "labels": ["ATS", "Match", "Quality"],
        "values": [
            result.ats_score,
            result.match_score,
            round(result.quality_checks.get("score", 0) * 100),
        ],
    }
    return render(
        request,
        "core/dashboard.html",
        {
            "result": result,
            "chart_payload": chart_payload,
            "quality_payload": quality_payload,
            "resume_review": build_resume_review(result),
        },
    )


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)

    analyses = (
        AnalysisResult.objects.filter(user=request.user)
        .select_related("job_description")
        .order_by("-created_at")[:8]
    )
    return render(request, "core/profile.html", {"form": form, "analyses": analyses})


@login_required
def analysis_detail_api(request, pk):
    result = get_object_or_404(AnalysisResult, pk=pk, user=request.user)
    return JsonResponse(_serialize_result(result))


@login_required
@require_POST
def resume_coach_api(request, pk):
    result = get_object_or_404(
        AnalysisResult.objects.select_related("resume", "job_description"),
        pk=pk,
        user=request.user,
    )
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    question = payload.get("question", "")
    return JsonResponse(answer_resume_question(result, question))


@login_required
@require_POST
def analyze_text_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    resume_text = payload.get("resume_text", "").strip()
    job_description = payload.get("job_description", "").strip()
    if not resume_text or not job_description:
        return JsonResponse(
            {"error": "Both resume_text and job_description are required."},
            status=400,
        )

    return JsonResponse(analyze_resume(resume_text, job_description))


@login_required
@require_POST
def upload_analysis_api(request):
    form = ResumeAnalysisForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    result = _create_analysis_from_form(request, form)
    if not isinstance(result, AnalysisResult):
        return JsonResponse({"errors": form.errors}, status=400)

    return JsonResponse(_serialize_result(result), status=201)


def _create_analysis_from_form(request, form):
    resume_file = form.cleaned_data["resume_file"]
    job_description_file = form.cleaned_data.get("job_description_file")
    pasted_job_description = form.cleaned_data.get("job_description", "").strip()

    try:
        resume_text = extract_text_from_upload(resume_file)
        uploaded_job_text = (
            extract_text_from_upload(job_description_file)
            if job_description_file
            else ""
        )
    except TextExtractionError as exc:
        form.add_error(None, str(exc))
        return None

    job_text = "\n".join(
        part for part in [pasted_job_description, uploaded_job_text] if part
    ).strip()
    if not job_text:
        form.add_error("job_description", "Add a job description to compare against.")
        return None

    analysis = analyze_resume(resume_text, job_text)
    job_description = JobDescription.objects.create(
        user=request.user,
        title=form.cleaned_data["job_title"],
        company=form.cleaned_data.get("company", ""),
        description=job_text,
        extracted_keywords=analysis["job_keywords"],
    )
    resume = Resume.objects.create(
        user=request.user,
        original_file=resume_file,
        extracted_text=resume_text,
        extracted_skills=analysis["extracted_skills"],
        education=analysis["education"],
        experience_years=analysis["experience_years"],
    )
    return AnalysisResult.objects.create(
        user=request.user,
        resume=resume,
        job_description=job_description,
        ats_score=analysis["ats_score"],
        match_score=analysis["match_score"],
        similarity_score=analysis["similarity_score"],
        extracted_skills=analysis["extracted_skills"],
        matched_skills=analysis["matched_skills"],
        missing_skills=analysis["missing_skills"],
        keyword_recommendations=analysis["keyword_recommendations"],
        suggestions=analysis["suggestions"],
        quality_checks=analysis["quality_checks"],
    )


def _serialize_result(result):
    return {
        "id": result.pk,
        "ats_score": result.ats_score,
        "match_score": result.match_score,
        "similarity_score": result.similarity_score,
        "extracted_skills": result.extracted_skills,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills,
        "keyword_recommendations": result.keyword_recommendations,
        "suggestions": result.suggestions,
        "quality_checks": result.quality_checks,
        "job": {
            "title": result.job_description.title,
            "company": result.job_description.company,
        },
        "created_at": result.created_at.isoformat(),
    }
