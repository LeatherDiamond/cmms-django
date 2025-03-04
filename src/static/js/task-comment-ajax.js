document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[id^='comment-form-']").forEach(form => {
        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const formData = new FormData(form);
            const url = form.getAttribute("data-url");

            const taskPk = form.id.split("-")[2];

            fetch(url, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
            })
            .then(response => response.json())
            .then(data => {
                toastr.options = {
                    "positionClass": "toast-bottom-left",
                    "closeButton": true,
                    "progressBar": true,
                    "timeOut": "5000"
                };

                if (data.success) {
                    document.querySelectorAll(`#comment-text-${taskPk}`).forEach(el => el.value = "");

                    fetch(window.location.href)
                        .then(response => response.text())
                        .then(html => {
                            let parser = new DOMParser();
                            let doc = parser.parseFromString(html, "text/html");
                            const newCommentLists = doc.querySelectorAll(`#comment-list-${taskPk}`);
                            const currentCommentLists = document.querySelectorAll(`#comment-list-${taskPk}`);
                            
                            newCommentLists.forEach((newCommentList, index) => {
                                if (currentCommentLists[index]) {
                                    currentCommentLists[index].innerHTML = newCommentList.innerHTML;
                                }
                            });
                        });

                    toastr.success(data.message);
                } else {
                    toastr.error("Wystąpił błąd. Proszę wypełnić poprawnie formularz.");
                }
            })
            .catch(error => {
                console.error("Błąd:", error);
                toastr.options = {
                    "positionClass": "toast-bottom-left",
                    "closeButton": true,
                    "progressBar": true,
                    "timeOut": "5000"
                };
                toastr.error("Wystąpił błąd. Spróbuj ponownie później.");
            });
        });
    });
});