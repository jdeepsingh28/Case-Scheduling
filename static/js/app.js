function fetchData() {
    const majorSelect = document.getElementById('majorSelect');
    const selectedMajor = majorSelect.value;

    // Mapping of majors to corresponding URLs
    const majorUrls = {
        "mechanical_aerospace_engineering": "https://bulletin.case.edu/engineering/mechanical-aerospace-engineering/aerospace-engineering-bse/#programrequirementstext",
        "computer_science": "https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext"
    };

    const selectedUrl = majorUrls[selectedMajor];
    console.log(`Selected URL: ${selectedUrl}`);  // Debugging statement

    if (selectedMajor && selectedUrl) {  // Check if a valid major and URL are selected
        fetch(`/get_course_data?url=${encodeURIComponent(selectedUrl)}`)
            .then(response => response.json())
            .then(data => {
                const contentDiv = document.getElementById('content');
                // Process and display the data (you might need to adjust this based on your data structure)
                contentDiv.innerHTML = `<pre>${JSON.stringify(data, null, 4)}</pre>`;
            });
    }
}
