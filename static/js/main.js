document.getElementById("image-upload").addEventListener("change", function(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.size > 5 * 1024 * 1024) {
            alert("File size exceeds 5MB limit.");
            return;
        }
        displayImagePreview(file);
    }
});

// Handle capture button click
document.getElementById("capture-btn").addEventListener("click", async function() {
    const modal = document.getElementById("camera-modal");
    const video = document.getElementById("camera-feed");
    modal.style.display = "block";

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.stream = stream; // Store stream for cleanup
    } catch (err) {
        console.error("Error accessing camera:", err);
        alert("Could not access camera: " + err.message);
        closeCameraModal();
    }
});

// Handle capture snap button
document.getElementById("capture-snap-btn").addEventListener("click", function() {
    const video = document.getElementById("camera-feed");
    const canvas = document.getElementById("capture-canvas");
    const context = canvas.getContext("2d");

    // Set canvas size to video dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob
    canvas.toBlob(function(blob) {
        const file = new File([blob], "captured_image.png", { type: "image/png" });
        displayImagePreview(file);
        closeCameraModal();
    }, "image/png");
});

// Handle cancel button
document.getElementById("capture-cancel-btn").addEventListener("click", function() {
    closeCameraModal();
});

// Function to display image preview
function displayImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = document.getElementById("image-preview");
        img.src = e.target.result;
        img.style.display = "block";
        document.getElementById("segment-btn").style.display = "inline-block";
        document.getElementById("reset-btn").style.display = "inline-block";
        // Update file input with captured file
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        document.getElementById("image-upload").files = dataTransfer.files;
    };
    reader.readAsDataURL(file);
}

// Function to close camera modal and stop stream
function closeCameraModal() {
    const modal = document.getElementById("camera-modal");
    const video = document.getElementById("camera-feed");
    if (video.stream) {
        video.stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        video.stream = null;
    }
    modal.style.display = "none";
}

document.getElementById("segment-btn").addEventListener("click", function() {
    const fileInput = document.getElementById("image-upload");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    document.getElementById("loader").style.display = "block";
    document.getElementById("result-placeholder").style.display = "none";
    document.getElementById("result-canvas").style.display = "none";
    document.getElementById("download-btn").style.display = "none";
    document.querySelector(".data-section").style.display = "none";
    document.querySelector(".opacity-control").style.display = "none";

    fetch("/predict", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response data:", data);
        document.getElementById("loader").style.display = "none";
        if (data.segmented_image && data.analysis) {
            const canvas = document.getElementById("result-canvas");
            const ctx = canvas.getContext("2d");
            const originalImg = new Image();
            const segmentedImg = new Image();

            let imagesLoaded = 0;
            let originalLoaded = false;

            const onImageLoad = () => {
                imagesLoaded++;
                if (imagesLoaded === 1 && !data.original_image) {
                    // Only segmented image available
                    canvas.width = segmentedImg.width;
                    canvas.height = segmentedImg.height;
                    updateCanvas();
                    canvas.style.display = "block";
                    document.getElementById("download-btn").href = canvas.toDataURL("image/png");
                    document.getElementById("download-btn").style.display = "inline-block";
                } else if (imagesLoaded === 2 || (imagesLoaded === 1 && originalLoaded)) {
                    // Both images loaded or original failed but segmented loaded
                    canvas.width = segmentedImg.width;
                    canvas.height = segmentedImg.height;
                    updateCanvas();
                    canvas.style.display = "block";
                    document.querySelector(".opacity-control").style.display = "block";
                    document.getElementById("download-btn").href = canvas.toDataURL("image/png");
                    document.getElementById("download-btn").style.display = "inline-block";
                }
            };

            originalImg.onerror = () => {
                console.error("Failed to load original image");
                alert("Error loading original image; showing segmented image only");
                originalLoaded = false;
            };
            segmentedImg.onerror = () => {
                console.error("Failed to load segmented image");
                alert("Error loading segmented image");
            };

            originalImg.onload = () => {
                originalLoaded = true;
                onImageLoad();
            };
            segmentedImg.onload = onImageLoad;

            segmentedImg.src = "data:image/png;base64," + data.segmented_image;
            if (data.original_image) {
                originalImg.src = "data:image/png;base64," + data.original_image;
            } else {
                console.warn("No original_image in response; using segmented image only");
                onImageLoad();
            }

            function updateCanvas() {
                const opacity = parseFloat(document.getElementById("opacity-slider").value);
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (originalLoaded && data.original_image) {
                    ctx.drawImage(originalImg, 0, 0);
                    ctx.globalAlpha = opacity;
                    ctx.drawImage(segmentedImg, 0, 0);
                    ctx.globalAlpha = 1.0;
                } else {
                    ctx.drawImage(segmentedImg, 0, 0);
                }
                document.getElementById("opacity-value").textContent = opacity.toFixed(2);
            }

            document.getElementById("opacity-slider").addEventListener("input", updateCanvas);

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
            const totalObjects = data.analysis.total_objects;
            noviceSummary.innerHTML = `<strong>Found ${totalObjects} objects:</strong> ` +
                Object.entries(data.analysis.object_counts)
                    .filter(([cls, count]) => count > 0 && cls !== "background")
                    .map(([cls, count]) => `${count} ${cls}${count > 1 ? 's' : ''}`)
                    .join(", ");

            const noviceObjects = document.getElementById("novice-objects");
            const icons = { person: "🧑", car: "🚗", cat: "🐱", dog: "🐶", chair: "🪑" };
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
        } else {
            console.error("Invalid response:", data);
            document.getElementById("result-placeholder").style.display = "block";
            alert("Error: " + (data.error || "Invalid response from server"));
        }
    })
    .catch(error => {
        console.error("Fetch error:", error);
        document.getElementById("loader").style.display = "none";
        document.getElementById("result-placeholder").style.display = "block";
        alert("An error occurred during segmentation: " + error.message);
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
    document.getElementById("result-canvas").style.display = "none";
    document.getElementById("result-placeholder").style.display = "block";
    document.getElementById("loader").style.display = "none";
    document.getElementById("download-btn").style.display = "none";
    document.querySelector(".data-section").style.display = "none";
    document.querySelector(".opacity-control").style.display = "none";
});