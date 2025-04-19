document.getElementById("image-upload").addEventListener("change", function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById("image-preview");
            img.src = e.target.result;
            img.style.display = "block";
            document.getElementById("segment-btn").style.display = "inline-block";
            document.getElementById("reset-btn").style.display = "inline-block";
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById("segment-btn").addEventListener("click", function() {
    const fileInput = document.getElementById("image-upload");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    document.getElementById("loader").style.display = "block";
    document.getElementById("result-placeholder").style.display = "none";
    document.getElementById("result-preview").style.display = "none";
    document.getElementById("download-btn").style.display = "none";
    document.querySelector(".data-section").style.display = "none";

    fetch("/predict", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loader").style.display = "none";
        if (data.segmented_image) {
            const resultImage = document.getElementById("result-preview");
            resultImage.src = "data:image/png;base64," + data.segmented_image;
            resultImage.style.display = "block";

            const downloadBtn = document.getElementById("download-btn");
            downloadBtn.href = resultImage.src;
            downloadBtn.style.display = "inline-block";

            const dataSection = document.querySelector(".data-section");
            dataSection.style.display = "block";
            document.getElementById("data-content").classList.add("active");

            // Detailed Analysis
            const objectCounts = document.getElementById("object-counts");
            objectCounts.innerHTML = "<h4 data-tooltip='Number of each object type found'>Detected Objects</h4>" +
                Object.entries(data.analysis.object_counts)
                    .filter(([cls, count]) => count > 0 && cls !== "background")
                    .map(([cls, count]) => `${cls}: ${count}`)
                    .join("<br>");

            const colorMapping = document.getElementById("color-mapping");
            colorMapping.innerHTML = "<h4 data-tooltip='Colors used for each object in the image'>Color Mapping</h4>" +
                Object.entries(data.analysis.color_mapping)
                    .map(([cls, color]) => `<span style="color:${color}">${cls}: ${color}</span>`)
                    .join("<br>");

            const areaAnalysis = document.getElementById("area-analysis");
            areaAnalysis.innerHTML = "<h4 data-tooltip='Percentage of the image each object covers'>Area Coverage</h4>" +
                Object.entries(data.analysis.area_percentages)
                    .filter(([cls, perc]) => parseFloat(perc) > 0 && cls !== "background")
                    .map(([cls, perc]) => `${cls}: ${perc}`)
                    .join("<br>");

            const summary = document.getElementById("summary");
            summary.textContent = `Total Objects Detected: ${data.analysis.total_objects}`;

            // Novice Analysis
            const noviceSummary = document.getElementById("novice-summary");
            const totalObjects = data.analysis.total_objects || Object.values(data.analysis.object_counts).reduce((sum, count) => sum + (count > 0 && count !== "background" ? count : 0), 0);
            noviceSummary.innerHTML = `<strong>Found ${totalObjects} objects:</strong> ` +
                Object.entries(data.analysis.object_counts)
                    .filter(([cls, count]) => count > 0 && cls !== "background")
                    .map(([cls, count]) => `${count} ${cls}${count > 1 ? 's' : ''}`)
                    .join(", ");

            const noviceObjects = document.getElementById("novice-objects");
            const icons = { person: "🧑", car: "🚗", cat: "🐱", dog: "🐶", chair: "🪑" }; // Add more as needed
            noviceObjects.innerHTML = "<h4 data-tooltip='Objects found in the image'>Objects</h4>" +
                Object.entries(data.analysis.object_counts)
                    .filter(([cls, count]) => count > 0 && cls !== "background")
                    .map(([cls, count]) => `${icons[cls] || "📍"} ${count} ${cls}${count > 1 ? 's' : ''}`)
                    .join("<br>");

            const noviceAreas = document.getElementById("novice-areas");
            noviceAreas.innerHTML = "<h4 data-tooltip='How much space each object covers'>Space Covered</h4>" +
                Object.entries(data.analysis.area_percentages)
                    .filter(([cls, perc]) => parseFloat(perc) > 0 && cls !== "background")
                    .map(([cls, perc]) => `<div class="area-label">${icons[cls] || "📍"} ${cls}: ${perc}</div><div class="area-bar" style="width:${parseFloat(perc)}%;background:${data.analysis.color_mapping[cls]}"></div>`)
                    .join("");
        } else if (data.error) {
            document.getElementById("result-placeholder").style.display = "block";
            alert("Error: " + data.error);
        }
    })
    .catch(error => {
        document.getElementById("loader").style.display = "none";
        document.getElementById("result-placeholder").style.display = "block";
        console.error("Error:", error);
        alert("An error occurred during segmentation.");
    });
});

document.getElementById("toggle-data").addEventListener("click", function() {
    const dataContent = document.getElementById("data-content");
    const isActive = dataContent.classList.toggle("active");
    this.textContent = `Toggle Analysis ${isActive ? "▲" : "▼"}`;
});

document.getElementById("detailed-toggle").addEventListener("click", function() {
    document.getElementById("detailed-analysis").style.display = "block";
    document.getElementById("novice-analysis").style.display = "none";
    this.classList.add("active");
    document.getElementById("novice-toggle").classList.remove("active");
});

document.getElementById("novice-toggle").addEventListener("click", function() {
    document.getElementById("detailed-analysis").style.display = "none";
    document.getElementById("novice-analysis").style.display = "block";
    this.classList.add("active");
    document.getElementById("detailed-toggle").classList.remove("active");
});

document.getElementById("reset-btn").addEventListener("click", function() {
    document.getElementById("image-upload").value = "";
    document.getElementById("image-preview").style.display = "none";
    document.getElementById("segment-btn").style.display = "none";
    document.getElementById("reset-btn").style.display = "none";
    document.getElementById("result-preview").style.display = "none";
    document.getElementById("result-placeholder").style.display = "block";
    document.getElementById("loader").style.display = "none";
    document.getElementById("download-btn").style.display = "none";
    document.querySelector(".data-section").style.display = "none";
});