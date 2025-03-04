document.addEventListener("DOMContentLoaded", function () {
    const attachmentsInput = document.getElementById("attachments");
    const fileList = document.getElementById("file-list");
    const errorContainer = document.querySelector(".attachment-error-container");
    const deleteAttachmentsInput = document.getElementById("delete-attachments");
    const form = attachmentsInput.closest("form");
    const maxFiles = 10;
    const maxSize = 24 * 1024 * 1024;
    
    let existingFiles = new Set();
    let files = new DataTransfer();
    
    document.querySelectorAll(".file-item").forEach(item => {
        existingFiles.add(item.getAttribute("data-existing-file"));
    });

    function displayError(message) {
        errorContainer.innerHTML = `<p class="attachment-error">${message}</p>`;
        errorContainer.classList.add("error-pulse");
        setTimeout(() => errorContainer.classList.remove("error-pulse"), 1000);
        form.dataset.valid = "false";
    }

    function clearError() {
        errorContainer.innerHTML = "";
        form.dataset.valid = "true";
    }

    function updateFileInput() {
        attachmentsInput.files = files.files;
        attachmentsInput.setAttribute("data-file-count", files.items.length + existingFiles.size);
    }

    function validateFiles() {
        clearError();
        let totalSize = 0;
        let fileNames = new Set([...existingFiles]);
        
        for (let i = 0; i < files.items.length; i++) {
            const file = files.items[i].getAsFile();
            if (fileNames.has(file.name)) {
                displayError(`Plik o nazwie ${file.name} już istnieje!`);
                return false;
            }
            fileNames.add(file.name);
            totalSize += file.size;
        }

        if (files.items.length + existingFiles.size > maxFiles) {
            displayError("Maksymalna liczba plików 10 została przekroczona.");
            return false;
        }
        if (totalSize > maxSize) {
            displayError("Łączny rozmiar plików przekracza limit 25 MB. ");
            return false;
        }
        return true;
    }

    attachmentsInput.addEventListener("change", function () {
        for (let i = 0; i < attachmentsInput.files.length; i++) {
            const file = attachmentsInput.files[i];
            
            if ([...existingFiles].some(f => f.includes(file.name))) {
                displayError(`Plik o nazwie ${file.name} już istnieje!`);
                continue;
            }
            
            files.items.add(file);
            const fileItem = document.createElement("div");
            fileItem.classList.add("file-item");
            fileItem.innerHTML = `<span>${file.name}</span><button type="button">X</button>`;
            fileList.appendChild(fileItem);
            
            fileItem.querySelector("button").addEventListener("click", function () {
                for (let j = 0; j < files.items.length; j++) {
                    if (files.items[j].getAsFile().name === file.name) {
                        files.items.remove(j);
                        break;
                    }
                }
                fileItem.remove();
                updateFileInput();
                validateFiles();
            });
        }
        updateFileInput();
        validateFiles();
    });

    document.querySelectorAll(".delete-existing").forEach(button => {
        button.addEventListener("click", function () {
            const fileItem = button.closest(".file-item");
            const fileId = fileItem.getAttribute("data-existing-file");
            
            if (fileId) {
                let deletedFiles = deleteAttachmentsInput.value ? deleteAttachmentsInput.value.split(",") : [];
                deletedFiles.push(fileId);
                deleteAttachmentsInput.value = deletedFiles.join(",");
                existingFiles.delete(fileId);
            }
            
            fileItem.remove();
            updateFileInput();
        });
    });
    
    form.addEventListener("submit", function (event) {
        if (!validateFiles()) {
            event.preventDefault();
            displayError("Nie można wysłać formularza z błędami!");
        }
    });
});