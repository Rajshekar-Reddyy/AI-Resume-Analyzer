import re


ACTION_VERBS = {
    "achieved",
    "analyzed",
    "automated",
    "built",
    "created",
    "delivered",
    "designed",
    "developed",
    "improved",
    "implemented",
    "increased",
    "launched",
    "led",
    "managed",
    "optimized",
    "reduced",
    "resolved",
}


def build_resume_review(result) -> list[dict]:
    resume_text = result.resume.extracted_text or ""
    snippets = _resume_snippets(resume_text)
    issues = []

    issues.extend(_missing_skill_issues(result, snippets))
    issues.extend(_keyword_issues(result, snippets))
    issues.extend(_quality_issues(result, snippets))
    issues.extend(_snippet_style_issues(snippets))

    if not issues:
        issues.append(
            {
                "label": "Strong targeted resume",
                "severity": "good",
                "snippet": snippets[0] if snippets else "Resume content looks aligned.",
                "reason": "The resume already covers the most important job signals detected by the analyzer.",
                "suggestion": "Fine-tune the top summary and first two bullets for this exact job title.",
                "example": "Full Stack Developer with Django, REST API, MySQL, and responsive UI experience.",
            }
        )

    return issues[:10]


def answer_resume_question(result, question: str) -> dict:
    question = (question or "").strip()
    review_items = build_resume_review(result)
    missing_skills = result.missing_skills[:6]
    keywords = result.keyword_recommendations[:6]
    quality = result.quality_checks or {}
    sections = quality.get("sections", {})

    if not question:
        return _coach_response(
            "Ask me what to improve, which skills to add, or how to rewrite a resume section.",
            review_items[:3],
        )

    normalized = question.lower()

    if any(term in normalized for term in ["skill", "missing", "add"]):
        if missing_skills:
            answer = (
                "Focus on the missing role-critical skills first: "
                + ", ".join(missing_skills)
                + ". Add them only where you can prove real usage through projects, internships, coursework, or certifications."
            )
        else:
            answer = "No major missing skills were detected. Improve the resume by making your existing skills more specific and outcome-driven."
        return _coach_response(answer, review_items[:4])

    if any(term in normalized for term in ["keyword", "ats", "score"]):
        if keywords:
            answer = (
                "To improve ATS alignment, naturally include these job keywords in your summary, skills, and project bullets: "
                + ", ".join(keywords)
                + ". Do not stuff keywords; connect each one to a concrete achievement."
            )
        else:
            answer = "Your keyword coverage is decent. The next improvement is stronger bullet quality and clearer evidence for matched skills."
        return _coach_response(answer, review_items[:4])

    if any(term in normalized for term in ["rewrite", "bullet", "project", "experience"]):
        answer = (
            "Rewrite weak bullets using this structure: action verb + technical task + tool + measurable result. "
            "Example: 'Built a Django dashboard with MySQL queries that reduced manual resume screening time by 40%.'"
        )
        return _coach_response(answer, _filter_review(review_items, ["Impact", "Action", "Measurable"]))

    if any(term in normalized for term in ["section", "summary", "education"]):
        missing_sections = [name for name, present in sections.items() if not present]
        if missing_sections:
            answer = "Add clear section headings for: " + ", ".join(section.title() for section in missing_sections) + "."
        else:
            answer = "Your main sections are present. Improve the summary by matching the job title and top 3 required skills."
        return _coach_response(answer, review_items[:4])

    answer = (
        "Best next move: target the resume to this job. Start with missing skills, then add job keywords, then rewrite the weakest bullets with measurable impact."
    )
    return _coach_response(answer, review_items[:5])


def _coach_response(answer: str, review_items: list[dict]) -> dict:
    return {
        "answer": answer,
        "actions": [
            item["suggestion"]
            for item in review_items
            if item.get("suggestion")
        ][:5],
        "examples": [
            item["example"]
            for item in review_items
            if item.get("example")
        ][:3],
    }


def _missing_skill_issues(result, snippets: list[str]) -> list[dict]:
    issues = []
    anchor = _best_anchor(snippets)
    for skill in result.missing_skills[:4]:
        issues.append(
            {
                "label": f"Missing skill: {skill}",
                "severity": "high",
                "snippet": anchor,
                "reason": f"The job description asks for {skill}, but the resume analyzer did not detect it.",
                "suggestion": f"Add {skill} to your skills or project bullets only if you have real experience with it.",
                "example": f"Implemented {skill} in a project to solve a specific business or technical problem.",
            }
        )
    return issues


def _keyword_issues(result, snippets: list[str]) -> list[dict]:
    issues = []
    anchor = _best_anchor(snippets)
    for keyword in result.keyword_recommendations[:3]:
        issues.append(
            {
                "label": f"Keyword gap: {keyword}",
                "severity": "medium",
                "snippet": anchor,
                "reason": "This keyword appears important for the job description but is weak or absent in the resume.",
                "suggestion": f"Use '{keyword}' naturally in a summary, skills list, or relevant project bullet.",
                "example": f"Built a {keyword}-related feature and explain the tool, task, and outcome.",
            }
        )
    return issues


def _quality_issues(result, snippets: list[str]) -> list[dict]:
    quality = result.quality_checks or {}
    issues = []
    sections = quality.get("sections", {})
    anchor = _best_anchor(snippets)

    for section, present in sections.items():
        if not present:
            issues.append(
                {
                    "label": f"Missing section: {section.title()}",
                    "severity": "high" if section in {"skills", "experience"} else "medium",
                    "snippet": anchor,
                    "reason": f"ATS parsers and recruiters expect a clear {section.title()} section.",
                    "suggestion": f"Add a separate '{section.title()}' heading with concise, scannable content.",
                    "example": _section_example(section),
                }
            )

    word_count = quality.get("word_count", 0)
    if word_count and word_count < 350:
        issues.append(
            {
                "label": "Resume is too short",
                "severity": "medium",
                "snippet": anchor,
                "reason": "A very short resume often lacks enough project evidence, tools, and outcomes.",
                "suggestion": "Expand your strongest 2-3 projects with tools used, responsibilities, and measurable impact.",
                "example": "Developed a Django resume analyzer with authentication, file uploads, NLP scoring, and Chart.js dashboards.",
            }
        )

    if not quality.get("has_bullets"):
        issues.append(
            {
                "label": "Bullet formatting not detected",
                "severity": "medium",
                "snippet": anchor,
                "reason": "Bullet points make achievements easier for recruiters and ATS systems to scan.",
                "suggestion": "Convert long paragraphs into short bullets starting with action verbs.",
                "example": "Built REST APIs in Django to upload resumes, store analysis results, and return JSON scoring data.",
            }
        )

    return issues


def _snippet_style_issues(snippets: list[str]) -> list[dict]:
    issues = []
    for snippet in snippets[:8]:
        lowered = snippet.lower()
        if len(snippet.split()) < 6:
            continue
        if not any(verb in lowered for verb in ACTION_VERBS):
            issues.append(
                {
                    "label": "Weak action wording",
                    "severity": "medium",
                    "snippet": snippet,
                    "reason": "This line does not clearly start from an achievement or action.",
                    "suggestion": "Rewrite it with a stronger action verb and the technical result.",
                    "example": "Improved resume-job matching by comparing extracted skills with job description keywords.",
                }
            )
        if not re.search(r"\d|%|\$|x\b", snippet.lower()) and len(snippet.split()) >= 10:
            issues.append(
                {
                    "label": "Add measurable impact",
                    "severity": "low",
                    "snippet": snippet,
                    "reason": "Recruiters trust bullets more when they include scale, frequency, speed, accuracy, or percentage impact.",
                    "suggestion": "Add a number if it is truthful: users, records, response time, accuracy, pages, APIs, or percentage improvement.",
                    "example": "Reduced manual screening time by 40% by adding automated ATS scoring and missing-skill detection.",
                }
            )
        if len(issues) >= 4:
            break
    return issues


def _resume_snippets(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ["Resume text could not be previewed. Upload a text-based PDF or DOCX for detailed marking."]

    sentences = [
        item.strip(" -")
        for item in re.split(r"(?<=[.!?])\s+|\s+-\s+", cleaned)
        if item.strip(" -")
    ]
    if len(sentences) >= 3:
        return [sentence[:260] for sentence in sentences[:16]]

    words = cleaned.split()
    return [" ".join(words[index : index + 28]) for index in range(0, min(len(words), 280), 28)]


def _best_anchor(snippets: list[str]) -> str:
    if not snippets:
        return "Resume preview unavailable."
    for snippet in snippets:
        if 8 <= len(snippet.split()) <= 38:
            return snippet
    return snippets[0]


def _section_example(section: str) -> str:
    examples = {
        "summary": "Full Stack Developer Intern skilled in Python, Django, JavaScript, MySQL, and REST APIs.",
        "skills": "Skills: Python, Django, JavaScript, HTML, CSS, MySQL, REST APIs, Git, GitHub.",
        "experience": "Built a Django web app with authentication, resume upload, NLP analysis, and dashboard charts.",
        "education": "B.Tech in Computer Science, University Name, 2026.",
    }
    return examples.get(section, f"Add a clear {section.title()} section with relevant details.")


def _filter_review(items: list[dict], labels: list[str]) -> list[dict]:
    filtered = [
        item
        for item in items
        if any(label.lower() in item.get("label", "").lower() for label in labels)
    ]
    return filtered or items[:4]
