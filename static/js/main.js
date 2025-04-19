document.getElementById("image-upload").addEventListener("change", function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById("image-preview");
            img.src = e.target.result;
            img.style.display = "block";  // Show the preview
            document.getElementById("segment-btn").style.display = "inline-block";  // Show segment button
        };
        reader.readAsDataURL(file);
    }
});

// When the Segment button is clicked
document.getElementById("segment-btn").addEventListener("click", function() {
    const fileInput = document.getElementById("image-upload");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Send the image to Flask backend for segmentation
    fetch("/predict", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.segmented_image) {
            const resultImage = document.getElementById("result-preview");
            resultImage.src = "data:image/png;base64," + data.segmented_image;  // Display the image
            document.querySelector(".result-section").style.display = "block";
        }
    })
    .catch(error => console.error("Error:", error));
});
