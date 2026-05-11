from .nlp import (
    extract_education,
    extract_experience_years,
    extract_keywords,
    extract_skills,
    section_coverage,
    similarity_score,
)


def analyze_resume(resume_text: str, job_text: str) -> dict:
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    resume_keywords = extract_keywords(resume_text, top_n=30)
    job_keywords = extract_keywords(job_text, top_n=30)

    matched_skills = sorted(set(resume_skills) & set(job_skills))
    missing_skills = sorted(set(job_skills) - set(resume_skills))

    if job_skills:
        skills_ratio = len(matched_skills) / len(job_skills)
    else:
        skills_ratio = _overlap_ratio(resume_keywords, job_keywords)

    keyword_ratio = _overlap_ratio(resume_keywords, job_keywords)
    similarity = similarity_score(resume_text, job_text)
    quality = resume_quality_score(resume_text)

    ats_score = round((skills_ratio * 45) + (keyword_ratio * 20) + (similarity * 20) + (quality["score"] * 15))
    match_score = round((skills_ratio * 60) + (similarity * 25) + (keyword_ratio * 15))

    return {
        "ats_score": _clamp_percent(ats_score),
        "match_score": _clamp_percent(match_score),
        "similarity_score": round(similarity, 3),
        "extracted_skills": resume_skills,
        "job_skills": job_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "resume_keywords": resume_keywords,
        "job_keywords": job_keywords,
        "keyword_recommendations": [
            keyword for keyword in job_keywords if keyword not in resume_keywords
        ][:12],
        "education": extract_education(resume_text),
        "experience_years": extract_experience_years(resume_text),
        "quality_checks": quality,
        "suggestions": build_suggestions(
            missing_skills=missing_skills,
            keyword_recommendations=[
                keyword for keyword in job_keywords if keyword not in resume_keywords
            ],
            quality=quality,
            match_score=_clamp_percent(match_score),
        ),
    }


def resume_quality_score(text: str) -> dict:
    words = text.split()
    coverage = section_coverage(text)
    length_score = 1 if 350 <= len(words) <= 1200 else 0.45 if len(words) >= 180 else 0.25
    section_score = sum(coverage.values()) / len(coverage)
    bullet_score = 1 if any(marker in text for marker in ["-", "*"]) else 0.45
    action_score = _action_verb_score(text)
    score = round((length_score * 0.25) + (section_score * 0.35) + (bullet_score * 0.15) + (action_score * 0.25), 2)

    return {
        "score": score,
        "word_count": len(words),
        "sections": coverage,
        "has_bullets": bullet_score == 1,
        "action_verb_score": action_score,
    }


def build_suggestions(
    missing_skills: list[str],
    keyword_recommendations: list[str],
    quality: dict,
    match_score: int,
) -> list[str]:
    suggestions = []
    if missing_skills:
        top_missing = ", ".join(missing_skills[:6])
        suggestions.append(f"Add evidence for these role-critical skills if you have them: {top_missing}.")
    if keyword_recommendations:
        top_keywords = ", ".join(keyword_recommendations[:6])
        suggestions.append(f"Mirror important job keywords naturally in your bullets: {top_keywords}.")
    missing_sections = [
        section.title()
        for section, present in quality.get("sections", {}).items()
        if not present
    ]
    if missing_sections:
        suggestions.append(f"Add clear resume sections for: {', '.join(missing_sections)}.")
    if quality.get("word_count", 0) < 350:
        suggestions.append("Expand project and work bullets with measurable impact, tools used, and outcomes.")
    if quality.get("word_count", 0) > 1200:
        suggestions.append("Trim older or less relevant details so the resume stays focused and scannable.")
    if not quality.get("has_bullets"):
        suggestions.append("Use concise bullet points so ATS parsers and recruiters can scan achievements quickly.")
    if quality.get("action_verb_score", 0) < 0.5:
        suggestions.append("Start more bullets with action verbs such as built, improved, automated, led, or delivered.")
    if match_score < 60:
        suggestions.append("Create a targeted version of the resume for this role instead of using a generic resume.")
    if not suggestions:
        suggestions.append("Strong match. Fine-tune the summary and top skills to echo this job description.")
    return suggestions


def _overlap_ratio(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not right_set:
        return 0.0
    return len(left_set & right_set) / len(right_set)


def _action_verb_score(text: str) -> float:
    action_verbs = {
        "built",
        "created",
        "designed",
        "developed",
        "implemented",
        "improved",
        "optimized",
        "automated",
        "launched",
        "led",
        "managed",
        "delivered",
        "reduced",
        "increased",
        "analyzed",
    }
    lowered = text.lower()
    hits = sum(1 for verb in action_verbs if verb in lowered)
    return min(hits / 5, 1)


def _clamp_percent(value: int) -> int:
    return max(0, min(100, int(value)))
