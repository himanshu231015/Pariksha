/**
 * Pariksha - Frontend Interactivity & Cascading Selectors
 * Pure Vanilla JavaScript (No React, No Framework Overhead)
 */

document.addEventListener("DOMContentLoaded", function () {
    initCascadingSelectors();
    initChatInterface();
    initFileUploadPreviews();
    initAutoDismissAlerts();
});

/**
 * Handle dynamic cascading dropdowns for University -> Program -> Branch -> Subject.
 */
function initCascadingSelectors() {
    const universitySelect = document.getElementById("id_university");
    const programSelect = document.getElementById("id_program");
    const branchSelect = document.getElementById("id_branch");
    const semesterSelect = document.getElementById("id_semester");
    const subjectSelect = document.getElementById("id_subject");

    if (programSelect && branchSelect) {
        programSelect.addEventListener("change", function () {
            const programId = this.value;
            if (!programId) return;

            // Fetch branches for this program
            fetch(`/academics/api/branches/?program_id=${programId}`)
                .then(res => res.json())
                .then(data => {
                    branchSelect.innerHTML = '<option value="">---------</option>';
                    data.branches.forEach(b => {
                        const opt = document.createElement("option");
                        opt.value = b.id;
                        opt.textContent = `${b.name} (${b.code})`;
                        branchSelect.appendChild(opt);
                    });
                })
                .catch(err => console.error("Error fetching branches:", err));

            // Fetch semesters for this program
            if (semesterSelect) {
                fetch(`/academics/api/semesters/?program_id=${programId}`)
                    .then(res => res.json())
                    .then(data => {
                        semesterSelect.innerHTML = '<option value="">---------</option>';
                        data.semesters.forEach(s => {
                            const opt = document.createElement("option");
                            opt.value = s.id;
                            opt.textContent = s.title;
                            semesterSelect.appendChild(opt);
                        });
                    })
                    .catch(err => console.error("Error fetching semesters:", err));
            }
        });
    }

    // When branch or semester changes, update subject choices
    function updateSubjects() {
        if (!subjectSelect) return;
        const branchId = branchSelect ? branchSelect.value : "";
        const semesterId = semesterSelect ? semesterSelect.value : "";

        if (!branchId && !semesterId) return;

        let url = `/academics/api/subjects/?`;
        if (branchId) url += `branch_id=${branchId}&`;
        if (semesterId) url += `semester_id=${semesterId}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                subjectSelect.innerHTML = '<option value="">---------</option>';
                data.subjects.forEach(s => {
                    const opt = document.createElement("option");
                    opt.value = s.id;
                    opt.textContent = `${s.code} - ${s.name}`;
                    subjectSelect.appendChild(opt);
                });
            })
            .catch(err => console.error("Error fetching subjects:", err));
    }

    if (branchSelect) branchSelect.addEventListener("change", updateSubjects);
    if (semesterSelect) semesterSelect.addEventListener("change", updateSubjects);
}

/**
 * Handle question suggestions chips and message submission in Ask Pariksha.
 */
function initChatInterface() {
    const chips = document.querySelectorAll(".chat-chip");
    const messageInput = document.querySelector("#id_message, textarea[name='message']");
    const chatHistory = document.querySelector(".chat-history");

    if (chips.length && messageInput) {
        chips.forEach(chip => {
            chip.addEventListener("click", function () {
                messageInput.value = this.getAttribute("data-question") || this.textContent.trim();
                messageInput.focus();
            });
        });
    }

    if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

/**
 * Show selected file name and format check before upload.
 */
function initFileUploadPreviews() {
    const fileInputs = document.querySelectorAll("input[type='file']");
    fileInputs.forEach(input => {
        input.addEventListener("change", function () {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
                if (file.size > 15 * 1024 * 1024) {
                    alert(`Selected file is ${sizeMb} MB. The maximum allowed limit is 15 MB.`);
                    this.value = "";
                }
            }
        });
    });
}

/**
 * Auto-dismiss transient bootstrap alert banners.
 */
function initAutoDismissAlerts() {
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                // Ignore if bootstrap is not yet initialized
            }
        }, 6000);
    });
}
