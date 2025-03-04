document.addEventListener("DOMContentLoaded", function () {
    const dataElement = document.getElementById("dashboard-data");
    if (!dataElement) return;

    try {
        const categoryStats = JSON.parse(dataElement.dataset.categoryStats);
        const priorityStats = JSON.parse(dataElement.dataset.priorityStats);

        const categoryContainer = document.querySelector(".chart-card.category");
        const priorityContainer = document.querySelector(".chart-card.priority");

        const categoryColors = {
            "Awaria": "#da261d",
            "Planowane": "#1da024",
        };

        const priorityColors = {
            "Wysoki": "#da261d",
            "Średni": "#ffcb22",
            "Niski": "#1da024",
        };

        if (categoryStats.length > 0) {
            const categoryData = {
                labels: categoryStats.map(item => item.category),
                datasets: [{
                    label: 'Kategorie',
                    data: categoryStats.map(item => item.count),
                    backgroundColor: categoryStats.map(item => categoryColors[item.category] || "#4bc0c0"),
                }]
            };
            new Chart(document.getElementById("categoryChart"), { type: 'doughnut', data: categoryData });
        } else {
            categoryContainer.innerHTML = "<p class='text-center text-muted'>Brak danych do wyświetlenia</p>";
        }

        if (priorityStats.length > 0) {
            const priorityData = {
                labels: priorityStats.map(item => item.priority),
                datasets: [{
                    label: 'Priorytety',
                    data: priorityStats.map(item => item.count),
                    backgroundColor: priorityStats.map(item => priorityColors[item.priority] || "#4bc0c0"),
                }]
            };
        
            new Chart(document.getElementById("priorityChart"), { 
                type: 'bar', 
                data: priorityData,
                options: {
                    plugins: {
                        legend: { display: false, position: 'top' }
                    }
                }
            });       
        
        } else {
            priorityContainer.innerHTML = "<p class='text-center text-muted'>Brak danych do wyświetlenia</p>";
        }

    } catch (error) {
        console.error("Błąd ładowania danych dla wykresów:", error);
    }
});
