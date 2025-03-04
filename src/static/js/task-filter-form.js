document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("#toggleFilter").forEach((filterHeader, index) => {
        const filterWrapper = document.querySelectorAll("#filterFormWrapper")[index];
        const toggleIcon = filterHeader.querySelector(".filter-toggle-icon");

        const isExpanded = localStorage.getItem(`filterFormExpanded_${index}`) === "true";

        if (isExpanded) {
            filterWrapper.classList.add("show", "no-transition");
            toggleIcon.classList.add("rotated");
        }

        setTimeout(() => filterWrapper.classList.remove("no-transition"), 50);

        filterHeader.addEventListener("click", function () {
            const isNowExpanded = filterWrapper.classList.toggle("show");
            localStorage.setItem(`filterFormExpanded_${index}`, isNowExpanded);
            toggleIcon.classList.toggle("rotated", isNowExpanded);
        });
    });
});