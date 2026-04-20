document.addEventListener('DOMContentLoaded', function () {
    // Initialize DataTables if the table exists
    if (document.getElementById('jobsTable')) {
        $('#jobsTable').DataTable({
            "order": [[0, "desc"]],
            "pageLength": 25,
            "language": {
                "search": "<i class='bi bi-search'></i> Search records:",
            }
        });
    }

    if (document.getElementById('profilesTable')) {
        $('#profilesTable').DataTable({
            "order": [[0, "asc"]],
            "pageLength": 25,
            "language": {
                "search": "<i class='bi bi-search'></i> Search records:",
            }
        });
    }

    // Polling logic for task status
    function pollTaskStatus(taskId) {
        const alert = document.getElementById('statusAlert');
        const btn = document.getElementById('scrapeBtn');
        const btnText = document.getElementById('btnText');

        const pollInterval = setInterval(() => {
            fetch(`/api/task_status/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    const status = data.status.toLowerCase();

                    if (status === 'completed') {
                        clearInterval(pollInterval);
                        alert.classList.replace('alert-primary', 'alert-success');
                        alert.innerHTML = '<i class="bi bi-check-circle-fill"></i> Data extracted successfully! Redirecting to your dashboard...';

                        // Auto-redirect to the appropriate view upon completion
                        setTimeout(() => {
                            if (data.task_type === 'profile') {
                                window.location.href = '/profiles';
                            } else {
                                window.location.href = '/dashboard';
                            }
                        }, 1500);

                    } else if (status === 'failed') {
                        clearInterval(pollInterval);
                        alert.classList.replace('alert-primary', 'alert-danger');
                        alert.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> Task failed to complete. Please check the logs or try again.';

                        btn.disabled = false;
                        if (btnText) btnText.innerHTML = '<i class="bi bi-lightning-charge"></i> Launch Scraper';
                    }
                })
                .catch(err => {
                    console.error("Polling error:", err);
                    clearInterval(pollInterval);
                    alert.classList.replace('alert-primary', 'alert-warning');
                    alert.innerHTML = '<i class="bi bi-wifi-off"></i> Lost connection while checking status. Task may still be running.';

                    btn.disabled = false;
                    if (btnText) btnText.innerHTML = '<i class="bi bi-arrow-repeat"></i> Try Again';
                });
        }, 1500); // Poll every 1.5 seconds
    }

    // Scrape Form Submit (Manual Trigger)
    const scrapeForm = document.getElementById('scrapeForm');

    // UI logic for Search Type
    const typeJob = document.getElementById('typeJob');
    const typeProfile = document.getElementById('typeProfile');
    const keywordInput = document.getElementById('keyword');
    const keywordHint = document.getElementById('keywordHint');
    const jobOnlyFilters = document.getElementById('jobOnlyFilters');

    if (typeJob && typeProfile) {
        function updateUIForType() {
            const expDiv = document.getElementById('experienceFilterDiv');
            if (typeProfile.checked) {
                keywordInput.placeholder = "e.g. Data Engineer, Database Admin";
                if (keywordHint) keywordHint.classList.remove('d-none');
                if (jobOnlyFilters) jobOnlyFilters.classList.add('d-none');
                if (expDiv) expDiv.classList.remove('d-none');
            } else {
                keywordInput.placeholder = "e.g. Data Scientist";
                if (keywordHint) keywordHint.classList.add('d-none');
                if (jobOnlyFilters) jobOnlyFilters.classList.remove('d-none');
                if (expDiv) expDiv.classList.add('d-none');
            }
        }
        typeJob.addEventListener('change', updateUIForType);
        typeProfile.addEventListener('change', updateUIForType);
        updateUIForType(); // initialize
    }

    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) return;

            const location = document.getElementById('location') ? document.getElementById('location').value.trim() : "";
            const company = document.getElementById('company') ? document.getElementById('company').value.trim() : "";
            const time_period = document.getElementById('time_period') ? document.getElementById('time_period').value : "";
            const salary = document.getElementById('salary') ? document.getElementById('salary').value.trim() : "";
            const task_type = document.querySelector('input[name="task_type"]:checked') ? document.querySelector('input[name="task_type"]:checked').value : "job";

            const btn = document.getElementById('scrapeBtn');
            const alert = document.getElementById('statusAlert');
            const btnText = document.getElementById('btnText');

            btn.disabled = true;
            if (btnText) {
                btnText.innerHTML = '<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> <span class="ms-1">Extracting...</span>';
            } else {
                btn.innerHTML = '<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> <span class="ms-1">Extracting...</span>';
            }

            fetch('/api/trigger_scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: keyword,
                    location: location,
                    company: company,
                    time_period: time_period,
                    salary: salary,
                    experience: document.getElementById('experience') ? document.getElementById('experience').value.trim() : "",
                    task_type: task_type
                })
            })
                .then(response => response.json())
                .then(data => {
                    alert.classList.remove('d-none', 'alert-danger', 'alert-success', 'alert-warning');
                    alert.classList.add('alert-primary', 'border', 'border-primary');
                    alert.innerHTML = '<div class="d-flex align-items-center"><div class="spinner-border spinner-border-sm text-primary me-3" role="status"></div> <div><strong>Task Working!</strong> Bots are currently navigating the web. Please wait...</div></div>';

                    pollTaskStatus(data.task_id);
                })
                .catch(error => {
                    alert.classList.remove('d-none', 'alert-success', 'alert-primary');
                    alert.classList.add('alert-danger');
                    alert.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Execution failed. Please try again.';

                    btn.disabled = false;
                    if (btnText) {
                        btnText.innerHTML = '<i class="bi bi-lightning-charge"></i> Launch Scraper';
                    }
                });
        });
    }

    // Task Deletion Logic (for manual tasks)
    const deleteTaskBtns = document.querySelectorAll('.delete-task-btn');
    deleteTaskBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            if (confirm("Are you sure you want to delete this task and all associated job records? This action cannot be undone.")) {
                const taskId = this.getAttribute('data-task-id');
                const row = document.getElementById(`task-${taskId}`);
                const originalHtml = this.innerHTML;

                this.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
                this.disabled = true;

                fetch(`/api/delete_task/${taskId}`, {
                    method: 'DELETE'
                })
                    .then(response => {
                        if (response.ok) {
                            row.style.transition = "opacity 0.4s";
                            row.style.opacity = "0";
                            setTimeout(() => {
                                row.remove();
                                if (document.querySelectorAll('.delete-task-btn').length === 0) {
                                    window.location.reload();
                                }
                            }, 400);
                        } else {
                            alert("Failed to delete task.");
                            this.innerHTML = originalHtml;
                            this.disabled = false;
                        }
                    })
                    .catch(err => {
                        console.error(err);
                        alert("An error occurred.");
                        this.innerHTML = originalHtml;
                        this.disabled = false;
                    });
            }
        });
    });

    // -------------------------------------------------------------
    // AUTOMATIONS JS LOGIC
    // -------------------------------------------------------------

    // Create new scheduled automation
    const autoForm = document.getElementById('automationForm');
    if (autoForm) {
        // UI logic for Search Type in Automation
        const autoTypeJob = document.getElementById('autoTypeJob');
        const autoTypeProfile = document.getElementById('autoTypeProfile');
        const autoKeywordInput = document.getElementById('autoKeyword');

        function updateAutoUIForType() {
            const isProfile = autoTypeProfile && autoTypeProfile.checked;
            const autoExpDiv = document.getElementById('autoExperienceDiv');
            if (autoKeywordInput) {
                autoKeywordInput.placeholder = isProfile ? "e.g. Data Engineer, Database Admin" : "e.g. Python Developer";
            }
            document.querySelectorAll('.auto-job-only').forEach(el => {
                if (isProfile) {
                    el.classList.add('d-none');
                } else {
                    el.classList.remove('d-none');
                }
            });
            if (autoExpDiv) {
                if (isProfile) autoExpDiv.classList.remove('d-none');
                else autoExpDiv.classList.add('d-none');
            }
        }

        if (autoTypeJob && autoTypeProfile) {
            autoTypeJob.addEventListener('change', updateAutoUIForType);
            autoTypeProfile.addEventListener('change', updateAutoUIForType);
            updateAutoUIForType(); // init
        }

        autoForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const keyword = document.getElementById('autoKeyword').value;
            const freq = document.getElementById('autoFrequency').value;
            const location = document.getElementById('autoLocation') ? document.getElementById('autoLocation').value : "";
            const company = document.getElementById('autoCompany') ? document.getElementById('autoCompany').value : "";
            const time_period = document.getElementById('autoTimePeriod') ? document.getElementById('autoTimePeriod').value : "";
            const salary = document.getElementById('autoSalary') ? document.getElementById('autoSalary').value : "";
            const task_type = document.querySelector('input[name="autoTaskType"]:checked') ? document.querySelector('input[name="autoTaskType"]:checked').value : "job";
            const btn = document.getElementById('saveAutoBtn');

            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
            btn.disabled = true;

            fetch('/api/automations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    keyword: keyword,
                    frequency: freq,
                    location: location,
                    company: company,
                    time_period: time_period,
                    salary: salary,
                    experience: document.getElementById('autoExperience') ? document.getElementById('autoExperience').value.trim() : "",
                    task_type: task_type
                })
            })
                .then(res => {
                    if (res.ok) {
                        window.location.reload();
                    } else {
                        alert("Failed to spawn automation.");
                        btn.innerHTML = '<i class="bi bi-check2"></i> Save Automation';
                        btn.disabled = false;
                    }
                });
        });
    }

    // Delete automation
    const deleteAutoBtns = document.querySelectorAll('.delete-auto-btn');
    deleteAutoBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            if (confirm("Delete this recurring schedule?")) {
                const autoId = this.getAttribute('data-id');
                const row = document.getElementById(`auto-${autoId}`);

                fetch(`/api/automations/${autoId}`, { method: 'DELETE' })
                    .then(res => {
                        if (res.ok) {
                            row.remove();
                        }
                    });
            }
        });
    });

    // Toggle active status
    const toggleAutoBtns = document.querySelectorAll('.toggle-auto-btn');
    toggleAutoBtns.forEach(btn => {
        btn.addEventListener('change', function () {
            const autoId = this.getAttribute('data-id');
            const label = this.nextElementSibling;

            fetch(`/api/automations/${autoId}/toggle`, { method: 'PUT' })
                .then(res => res.json())
                .then(data => {
                    if (data.status) {
                        label.innerHTML = '<span class="text-success fw-bold">Active</span>';
                    } else {
                        label.innerHTML = '<span class="text-muted">Paused</span>';
                    }
                });
        });
    });
});
