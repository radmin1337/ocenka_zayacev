import os
from flask import Flask, render_template_string, request, jsonify, send_from_directory
import requests

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1510044943584989328/QRtN_M5kWPZkvrVuSMFTM1HoXNebOcqgdeO3M6suT0iBhW7IedwgB6QFLtUAAMtoxzJ7"

IMAGES_FOLDER = "images"


@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGES_FOLDER, filename)


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/")
def index():
    files = [f for f in os.listdir(IMAGES_FOLDER)
             if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Оценка Заяцев</title>

<link rel="icon" type="image/x-icon" href="/static/favicon.ico">

<style>
body {
    margin:0;
    background:#111;
    color:white;
    font-family:Arial;
    text-align:center;
}

.container {
    margin-top:50px;
}

img {
    max-height:400px;
    border-radius:10px;
    opacity:0;
    transition:opacity 0.4s ease;
}

img.loaded {
    opacity:1;
}

.stars {
    font-size:40px;
    cursor:pointer;
    color:gray;
}

.star.active {
    color:gold;
}

button {
    margin-top:20px;
    padding:10px 20px;
    font-size:16px;
    background:#222;
    color:white;
    border:1px solid #444;
    border-radius:5px;
    cursor:pointer;
}

button:hover {
    background:#333;
}

/* Экран загрузки */
.loader {
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background:#111;
    display:flex;
    align-items:center;
    justify-content:center;
    z-index:999;
}

.spinner {
    border:6px solid #333;
    border-top:6px solid gold;
    border-radius:50%;
    width:60px;
    height:60px;
    animation:spin 1s linear infinite;
}

@keyframes spin {
    0% { transform:rotate(0deg); }
    100% { transform:rotate(360deg); }
}
</style>
</head>

<body>

<div class="loader" id="loader">
    <div class="spinner"></div>
</div>

<div class="container">
    <img id="image"><br>
    <h2 id="title"></h2>
    <div class="stars" id="stars"></div>
    <button onclick="nextImage()">Далее</button>
</div>

<script>
let images = {{ files|tojson }};
let current = 0;
let ratings = {};
let selectedRating = 0;

function loadImage() {
    if (current >= images.length) {
        fetch("/submit", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify(ratings)
        }).then(()=> {
            document.body.innerHTML = "<h1>Спасибо за оценку!</h1>";
        });
        return;
    }

    selectedRating = 0;

    let loader = document.getElementById("loader");
    loader.style.display = "flex";

    let img = document.getElementById("image");
    img.classList.remove("loaded");

    img.onload = function() {
        loader.style.display = "none";
        img.classList.add("loaded");
    };

    img.src = "/images/" + images[current];

    document.getElementById("title").innerText =
        images[current].split(".").slice(0,-1).join(".");

    renderStars();
}

function renderStars() {
    let starsDiv = document.getElementById("stars");
    starsDiv.innerHTML = "";
    for (let i=1; i<=5; i++) {
        let span = document.createElement("span");
        span.innerHTML = "★";
        span.className = "star";
        if (i <= selectedRating) span.classList.add("active");
        span.onclick = ()=> {
            selectedRating = i;
            renderStars();
        };
        starsDiv.appendChild(span);
    }
}

function nextImage() {
    if (selectedRating === 0) {
        alert("Поставь оценку!");
        return;
    }
    ratings[images[current]] = selectedRating;
    current++;
    loadImage();
}

window.onload = loadImage;
</script>

</body>
</html>
""", files=files)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    message = "Новые оценки изображений\n\n"

    for name, rating in data.items():
        message += f"{name} — {rating} ⭐\n"

    message += f"\nIP:\n{ip}\n\nBrowser:\n{user_agent}"

    requests.post(WEBHOOK_URL, json={"content": message})
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
