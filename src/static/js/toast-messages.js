document.addEventListener("DOMContentLoaded", function () {
    const toastContainer = document.getElementById("toast-messages");
    if (!toastContainer) return;

    try {
        const messages = JSON.parse(toastContainer.dataset.messages);
        if (messages.length > 0) {
            toastr.options = {
                "positionClass": "toast-bottom-left",
                "closeButton": true,
                "progressBar": true,
                "timeOut": "5000"
            };

            messages.forEach(msg => {
                toastr[msg.type](msg.text);
            });
        }
    } catch (error) {
        console.error("Błąd przetwarzania wiadomości toast:", error);
    }
});
