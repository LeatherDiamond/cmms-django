document.addEventListener("DOMContentLoaded", function () {
    function showElementWithAnimation(element) {
        element.classList.remove("d-none");
        element.style.opacity = "0";
        element.style.transform = "scale(0.95)";
        setTimeout(() => {
            element.style.transition = "opacity 0.3s ease, transform 0.3s ease";
            element.style.opacity = "1";
            element.style.transform = "scale(1)";
        }, 10);
    }

    function hideElementWithAnimation(element, callback) {
        element.style.opacity = "0";
        element.style.transform = "scale(0.95)";
        setTimeout(() => {
            element.classList.add("d-none");
            element.style.transition = "";
            if (callback) callback();
        }, 300);
    }

    document.querySelectorAll(".show-decline-confirmation").forEach(button => {
        button.addEventListener("click", function () {
            const taskId = this.dataset.taskId;
            const taskCard = this.closest(".card-body");
            taskCard.querySelector(".buttons-container").classList.add("d-none");
            showElementWithAnimation(document.getElementById(`confirmDecline${taskId}`));
        });
    });

    document.querySelectorAll(".cancel-decline").forEach(button => {
        button.addEventListener("click", function () {
            const taskId = this.dataset.taskId;
            const taskCard = this.closest(".card-body");
            hideElementWithAnimation(document.getElementById(`confirmDecline${taskId}`), () => {
                taskCard.querySelector(".buttons-container").classList.remove("d-none");
            });
        });
    });

    document.querySelectorAll(".show-confirmation").forEach(button => {
        button.addEventListener("click", function () {
            const taskId = this.dataset.taskId;
            const taskCard = this.closest(".card-body");
            taskCard.querySelector(".buttons-container").classList.add("d-none");
            showElementWithAnimation(document.getElementById(`confirmDelete${taskId}`));
        });
    });

    document.querySelectorAll(".cancel-delete").forEach(button => {
        button.addEventListener("click", function () {
            const taskId = this.dataset.taskId;
            const taskCard = this.closest(".card-body");
            hideElementWithAnimation(document.getElementById(`confirmDelete${taskId}`), () => {
                taskCard.querySelector(".buttons-container").classList.remove("d-none");
            });
        });
    });
});