import os
from flask import Flask, render_template_string, request, jsonify, send_from_directory
import requests
from PIL import Image

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1510044943584989328/QRtN_M5kWPZkvrVuSMFTM1HoXNebOcqgdeO3M6suT0iBhW7IedwgB6QFLtUAAMtoxzJ7"

IMAGES_FOLDER = "images"
THUMB_FOLDER = "thumbnails"
MAX_SIZE = (1000, 1000)

os.makedirs(THUMB_FOLDER, exist_ok=True)

def generate_thumbnails():
    print("Генерация изображений...")
    for filename in os.listdir(IMAGES_FOLDER):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            original_path = os.path.join(IMAGES_FOLDER, filename)
            thumb_path = os.path.join(THUMB_FOLDER, filename)

            if not os.path.exists(thumb_path):
                try:
                    with Image.open(original_path) as img:
                        img.thumbnail(MAX_SIZE)
                        img.save(thumb_path, optimize=True, quality=80)
                        print("Создано:", filename)
                except Exception as e:
                    print("Ошибка:", filename, e)
    print("Готово ✅")


@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(THUMB_FOLDER, filename, max_age=86400)


@app.route("/")
def index():

    files = [
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
    ]

    if not files:
        return "<h1 style='color:white;background:#111;text-align:center;padding:50px;'>Нет изображений</h1>"

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Оценка</title>

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

.image-container {
    flex:1;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    padding:20px;
}

img {
    max-width:90%;
    max-height:70vh;
    object-fit:contain;
    border-radius:10px;
}

h2 {
    margin-top:20px;
}

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
</style>
</head>

<body>

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

function preloadNext() {
    if (current + 1 < images.length) {
        let img = new Image();
        img.src = "/images/" + images[current + 1];
    }
}

function loadImage() {

    selectedRating = 0;

    let img = document.getElementById("image");

    img.onload = function() {
        preloadNext();
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

    message = "Новые оценки\\n\\n"

    for name, rating in data.items():
        message += f"{name} — {rating} ⭐\\n"

    message += f"\\nIP:\\n{ip}\\n\\nBrowser:\\n{user_agent}"

    requests.post(WEBHOOK_URL, json={"content": message})
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    generate_thumbnails()
    app.run(host="0.0.0.0", port=10000)
