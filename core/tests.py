from django.test import SimpleTestCase

from .services.scoring import analyze_resume


class ResumeScoringTests(SimpleTestCase):
    def test_analysis_detects_matched_and_missing_skills(self):
        resume = """
        Python developer with Django, REST API, MySQL, Git, and data analysis experience.
        Built dashboards and improved reporting workflows.
        """
        job = """
        We need a Python Django engineer with REST API, Docker, AWS, MySQL, and unit testing.
        """

        result = analyze_resume(resume, job)

        self.assertIn("python", result["matched_skills"])
        self.assertIn("django", result["matched_skills"])
        self.assertIn("docker", result["missing_skills"])
        self.assertGreater(result["ats_score"], 0)
        self.assertGreater(result["match_score"], 0)
