document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();

    var formData = new FormData();
    formData.append('image', document.getElementById('image').files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            // Display disease details
            document.getElementById('disease_name').textContent = data.name;
            document.getElementById('disease_description').textContent = data.description;
            document.getElementById('uploaded_image').src = data.image_path;
            document.getElementById('uploaded_image').style.display = 'block';

            // Plot the graph if spread_data is available
            if (data.spread_data) {
                var ctx = document.getElementById('myChart').getContext('2d');
                var chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.spread_data.years,
                        datasets: [{
                            label: 'Cases',
                            data: data.spread_data.cases,
                            backgroundColor: 'rgba(54, 162, 235, 0.8)', // Blue color for bars
                            borderColor: 'rgba(54, 162, 235, 1)', // Darker blue color for borders
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    color: 'rgba(0, 0, 0, 0.8)' // Darker color for y-axis labels
                                }
                            },
                            x: {
                                ticks: {
                                    color: 'rgba(0, 0, 0, 0.8)' // Darker color for x-axis labels
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: {
                                    color: 'rgba(0, 0, 0, 0.8)' // Darker color for legend text
                                }
                            }
                        }
                    }
                });
            }
        }
    })
    .catch(error => console.error('Error:', error));
});
