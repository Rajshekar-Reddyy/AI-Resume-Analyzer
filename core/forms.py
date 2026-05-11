from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_JOB_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=80, required=False)
    last_name = forms.CharField(max_length=80, required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class ResumeAnalysisForm(forms.Form):
    resume_file = forms.FileField(
        label="Resume",
        help_text="Upload a PDF or DOCX resume.",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.docx"}),
    )
    job_title = forms.CharField(max_length=160)
    company = forms.CharField(max_length=160, required=False)
    job_description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 9}),
        required=False,
        help_text="Paste the job description here or upload it below.",
    )
    job_description_file = forms.FileField(
        label="Job description file",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.docx,.txt"}),
    )

    def clean_resume_file(self):
        uploaded_file = self.cleaned_data["resume_file"]
        self._validate_file(uploaded_file, ALLOWED_RESUME_EXTENSIONS)
        return uploaded_file

    def clean_job_description_file(self):
        uploaded_file = self.cleaned_data.get("job_description_file")
        if uploaded_file:
            self._validate_file(uploaded_file, ALLOWED_JOB_EXTENSIONS)
        return uploaded_file

    def clean(self):
        cleaned_data = super().clean()
        pasted_description = cleaned_data.get("job_description", "").strip()
        uploaded_description = cleaned_data.get("job_description_file")
        if not pasted_description and not uploaded_description:
            raise forms.ValidationError(
                "Paste a job description or upload a PDF, DOCX, or TXT job description file."
            )
        return cleaned_data

    @staticmethod
    def _validate_file(uploaded_file, allowed_extensions):
        extension = f".{uploaded_file.name.split('.')[-1].lower()}"
        if extension not in allowed_extensions:
            allowed = ", ".join(sorted(allowed_extensions))
            raise forms.ValidationError(f"Unsupported file type. Allowed: {allowed}.")
        if uploaded_file.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError("File is too large. Keep uploads under 5 MB.")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
