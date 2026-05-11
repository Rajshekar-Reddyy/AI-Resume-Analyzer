(function () {
    const navToggle = document.querySelector("[data-nav-toggle]");
    const navLinks = document.querySelector("[data-nav-links]");
    const themeToggle = document.querySelector("[data-theme-toggle]");
    const charts = [];

    if (navToggle && navLinks) {
        navToggle.addEventListener("click", () => {
            navLinks.classList.toggle("open");
        });
    }

    function refreshIcons() {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function currentTheme() {
        return document.documentElement.dataset.theme || "light";
    }

    function setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        localStorage.setItem("resume-analyzer-theme", theme);
        if (themeToggle) {
            themeToggle.innerHTML = theme === "dark"
                ? '<i data-lucide="sun"></i>'
                : '<i data-lucide="moon"></i>';
        }
        refreshIcons();
        rerenderCharts();
    }

    if (themeToggle) {
        setTheme(currentTheme());
        themeToggle.addEventListener("click", () => {
            setTheme(currentTheme() === "dark" ? "light" : "dark");
        });
    } else {
        refreshIcons();
    }

    initDropzones();
    animateScoreRings();
    initScrollReveal();
    initResumeCoach();

    function parseJsonScript(id) {
        const node = document.getElementById(id);
        if (!node) {
            return null;
        }
        return JSON.parse(node.textContent);
    }

    function chartColors() {
        const style = getComputedStyle(document.documentElement);
        return {
            primary: style.getPropertyValue("--primary").trim(),
            teal: style.getPropertyValue("--teal").trim(),
            amber: style.getPropertyValue("--amber").trim(),
            coral: style.getPropertyValue("--coral").trim(),
            green: style.getPropertyValue("--green").trim(),
            ink: style.getPropertyValue("--ink").trim(),
            muted: style.getPropertyValue("--muted").trim(),
            line: style.getPropertyValue("--line").trim(),
        };
    }

    function renderDashboard() {
        if (!window.Chart) {
            return;
        }

        charts.splice(0).forEach((chart) => chart.destroy());

        const skills = parseJsonScript("skills-chart-data");
        const quality = parseJsonScript("quality-chart-data");
        const skillsCanvas = document.getElementById("skillsChart");
        const qualityCanvas = document.getElementById("qualityChart");
        const colors = chartColors();

        window.Chart.defaults.color = colors.muted;
        window.Chart.defaults.font.family = "Inter";

        if (skills && skillsCanvas) {
            charts.push(new Chart(skillsCanvas, {
                type: "doughnut",
                data: {
                    labels: skills.labels,
                    datasets: [
                        {
                            data: skills.values,
                            backgroundColor: [colors.green, colors.amber],
                            borderWidth: 0,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                boxWidth: 12,
                                font: { family: "Inter", weight: "700" },
                            },
                        },
                    },
                    cutout: "68%",
                },
            }));
        }

        if (quality && qualityCanvas) {
            charts.push(new Chart(qualityCanvas, {
                type: "bar",
                data: {
                    labels: quality.labels,
                    datasets: [
                        {
                            data: quality.values,
                            backgroundColor: [colors.primary, colors.teal, colors.coral],
                            borderRadius: 8,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: { color: colors.line },
                        },
                        x: {
                            grid: { display: false },
                        },
                    },
                    plugins: {
                        legend: { display: false },
                    },
                },
            }));
        }
    }

    function rerenderCharts() {
        if (document.getElementById("skillsChart") || document.getElementById("qualityChart")) {
            renderDashboard();
        }
    }

    function initDropzones() {
        document.querySelectorAll("[data-dropzone]").forEach((dropzone) => {
            const input = dropzone.querySelector('input[type="file"]');
            const fileName = dropzone.querySelector("[data-file-name]");
            const trigger = dropzone.querySelector("[data-file-trigger]");

            if (!input) {
                return;
            }

            function updateName() {
                const selected = input.files && input.files.length ? input.files[0].name : "No file selected";
                if (fileName) {
                    fileName.textContent = selected;
                }
                dropzone.classList.toggle("has-file", selected !== "No file selected");
            }

            input.addEventListener("change", updateName);

            if (trigger) {
                trigger.addEventListener("click", () => input.click());
            }

            ["dragenter", "dragover"].forEach((eventName) => {
                dropzone.addEventListener(eventName, (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    dropzone.classList.add("is-dragover");
                });
            });

            ["dragleave", "drop"].forEach((eventName) => {
                dropzone.addEventListener(eventName, (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    dropzone.classList.remove("is-dragover");
                });
            });

            dropzone.addEventListener("drop", (event) => {
                const files = event.dataTransfer && event.dataTransfer.files;
                if (files && files.length) {
                    input.files = files;
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                }
            });
        });
    }

    function animateScoreRings() {
        document.querySelectorAll("[data-score]").forEach((ring) => {
            const target = Number(ring.dataset.score || 0);
            const value = ring.querySelector("[data-score-value]");
            const duration = 950;
            const start = performance.now();

            function frame(now) {
                const progress = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.round(target * eased);
                ring.style.setProperty("--animated-score", `${current}%`);
                if (value) {
                    value.textContent = current;
                }
                if (progress < 1) {
                    requestAnimationFrame(frame);
                }
            }

            requestAnimationFrame(frame);
        });
    }

    function initScrollReveal() {
        const revealItems = document.querySelectorAll("[data-reveal]");
        if (!revealItems.length) {
            return;
        }

        if (!("IntersectionObserver" in window)) {
            revealItems.forEach((item) => item.classList.add("is-visible"));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.14 });

        revealItems.forEach((item) => observer.observe(item));
    }

    function initResumeCoach() {
        const form = document.querySelector("[data-coach-form]");
        const chat = document.querySelector("[data-coach-chat]");
        if (!form || !chat) {
            return;
        }

        const input = form.querySelector('input[name="question"]');
        const submitButton = form.querySelector('button[type="submit"]');
        const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]');
        const quickPrompts = document.querySelectorAll("[data-coach-prompt]");

        quickPrompts.forEach((button) => {
            button.addEventListener("click", () => {
                input.value = button.dataset.coachPrompt || "";
                form.requestSubmit();
            });
        });

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const question = input.value.trim();
            if (!question) {
                input.focus();
                return;
            }

            appendCoachMessage(chat, "user", question);
            input.value = "";
            setCoachLoading(submitButton, true);
            const loading = appendCoachMessage(chat, "ai", "Thinking through your resume and this job description...");

            try {
                const response = await fetch(form.dataset.coachUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrf ? csrf.value : "",
                    },
                    body: JSON.stringify({ question }),
                });

                if (!response.ok) {
                    throw new Error("Coach request failed.");
                }

                const data = await response.json();
                loading.remove();
                appendCoachAnswer(chat, data);
            } catch (error) {
                loading.remove();
                appendCoachMessage(chat, "ai", "I could not answer that yet. Please refresh the page and try again.");
            } finally {
                setCoachLoading(submitButton, false);
            }
        });
    }

    function setCoachLoading(button, isLoading) {
        if (!button) {
            return;
        }
        button.disabled = isLoading;
        button.innerHTML = isLoading
            ? '<i data-lucide="loader-circle"></i> Asking'
            : '<i data-lucide="send"></i> Ask';
        refreshIcons();
    }

    function appendCoachMessage(chat, type, text) {
        const message = document.createElement("article");
        message.className = `coach-message coach-message-${type}`;

        const icon = document.createElement("i");
        icon.setAttribute("data-lucide", type === "user" ? "user-round" : "sparkles");

        const paragraph = document.createElement("p");
        paragraph.textContent = text;

        message.append(icon, paragraph);
        chat.appendChild(message);
        refreshIcons();
        chat.scrollTop = chat.scrollHeight;
        return message;
    }

    function appendCoachAnswer(chat, data) {
        const message = document.createElement("article");
        message.className = "coach-message coach-message-ai";

        const icon = document.createElement("i");
        icon.setAttribute("data-lucide", "sparkles");

        const content = document.createElement("div");
        content.className = "coach-answer-block";

        const answer = document.createElement("p");
        answer.textContent = data.answer || "Here are the best resume improvements for this job.";
        content.appendChild(answer);

        if (data.actions && data.actions.length) {
            content.appendChild(coachList("Action steps", data.actions));
        }

        if (data.examples && data.examples.length) {
            content.appendChild(coachList("Example rewrites", data.examples));
        }

        message.append(icon, content);
        chat.appendChild(message);
        refreshIcons();
        chat.scrollTop = chat.scrollHeight;
    }

    function coachList(title, items) {
        const wrapper = document.createElement("div");
        const heading = document.createElement("strong");
        heading.textContent = title;
        const list = document.createElement("ul");

        items.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            list.appendChild(li);
        });

        wrapper.append(heading, list);
        return wrapper;
    }

    window.ResumeAnalyzerCharts = {
        renderDashboard,
    };
})();
