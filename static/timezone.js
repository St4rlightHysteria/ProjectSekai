function timezoneSaved() {
    document.getElementById("valid").innerText = "Timezone saved!"
}

function displayUTCTime() {
    var now = new Date();
    var utcTime = now.toUTCString();
    document.getElementById("utcTime").innerHTML = utcTime;
}

// Update the UTC time every second
setInterval(displayUTCTime, 1000);
