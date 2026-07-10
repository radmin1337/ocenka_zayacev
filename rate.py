import os
from flask import Flask, render_template_string, request, jsonify, send_from_directory
import requests
from PIL import Image

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1510044943584989328/QRtN_M5kWPZkvrVuSMFTM1HoXNebOcqgdeO3M6suT0iBhW7IedwgB6QFLtUAAMtoxzJ7"

IMAGES_FOLDER = "images"
THUMB_FOLDER = "thumbnails"
MAX_SIZE = (1200, 1200)

os.makedirs(THUMB_FOLDER, exist_ok=True)

@app.route("/images/<path:filename>")
def images(filename):
    original_path = os.path.join(IMAGES_FOLDER, filename)
    thumb_path = os.path.join(THUMB_FOLDER, filename)

    if not os.path.exists(original_path):
        return "Файл не найден", 404

    if not os.path.exists(thumb_path):
        try:
            with Image.open(original_path) as img:
                img.thumbnail(MAX_SIZE)
                img.save(thumb_path, optimize=True, quality=85)
        except Exception as e:
            return f"Ошибка обработки изображения: {e}", 500

    return send_from_directory(THUMB_FOLDER, filename)


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/")
def index():
    files = [
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
    ]

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
    display:flex;
    flex-direction:column;
    height:100vh;
}

/* Контейнер картинки */
.image-container {
    flex:1;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    overflow:hidden;
    padding:20px;
}

img {
    max-width:90%;
    max-height:70vh;
    object-fit:contain;
    border-radius:10px;
    opacity:0;
    transition:opacity 0.4s ease;
}

img.loaded {
    opacity:1;
}

h2 {
    margin-top:20px;
}

/* Панель оценки */
.panel {
    padding:20px;
    background:#000;
    border-top:1px solid #333;
    text-align:center;
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
    margin-top:15px;
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

/* Лоадер */
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

<div class="image-container">
    <img id="image">
    <h2 id="title"></h2>
</div>

<div class="panel">
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
            document.body.innerHTML = "<h1 style='margin:auto'>Спасибо за оценку!</h1>";
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

    message = "Новые оценки изображений\\n\\n"

    for name, rating in data.items():
        message += f"{name} — {rating} ⭐\\n"

    message += f"\\nIP:\\n{ip}\\n\\nBrowser:\\n{user_agent}"

    requests.post(WEBHOOK_URL, json={"content": message})
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
