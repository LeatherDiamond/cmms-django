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

    document.querySelectorAll(".show-building-confirmation").forEach(button => {
        button.addEventListener("click", function () {
            const buildingId = this.dataset.buildingId;
            const buildingCard = this.closest(".card-body");
            buildingCard.querySelector(".buttons-container").classList.add("d-none");
            showElementWithAnimation(document.getElementById(`confirmBuildingDelete${buildingId}`));
        });
    });

    document.querySelectorAll(".cancel-delete").forEach(button => {
        button.addEventListener("click", function () {
            const buildingId = this.dataset.buildingId;
            const buildingCard = this.closest(".card-body");
            hideElementWithAnimation(document.getElementById(`confirmBuildingDelete${buildingId}`), () => {
                buildingCard.querySelector(".buttons-container").classList.remove("d-none");
            });
        });
    });
});