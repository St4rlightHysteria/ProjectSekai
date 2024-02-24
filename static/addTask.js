function validateForm() {
    var title = document.getElementById("title").value;
    var desc = document.getElementById("desc").value;
    var date = document.getElementById("date").value;
    var time = document.getElementById("time").value;

    // Reset error messages
    document.getElementById("titleError").innerText = "";
    document.getElementById("descError").innerText = "";
    document.getElementById("dateError").innerText = "";
    document.getElementById("timeError").innerText = "";

    var isValid = true;

    if (!title) {
        document.getElementById("titleError").innerText = "Task title is required.";
        isValid = false;
    }

    if (!desc) {
        document.getElementById("descError").innerText = "Task description is required.";
        isValid = false;
    }

    if (!date) {
        document.getElementById("dateError").innerText = "Deadline date is required.";
        isValid = false;
    }

    if (!time) {
        document.getElementById("timeError").innerText = "Deadline time is required.";
        isValid = false;
    }

    return isValid;
}
