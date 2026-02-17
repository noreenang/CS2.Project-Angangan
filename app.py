
from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from werkzeug.utils import secure_filename

# ---------------------
# Configuration
# ---------------------
app = Flask(__name__)
app.secret_key = "CS2_PROJECT_SECRET_KEY"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

MOVIE_FILE = "movies.json"
USER_FILE = "users.json"

# ---------------------
# Helper Functions
# ---------------------
def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------
# Routes
# ---------------------

# Homepage - display movies
@app.route("/")
def index():
    movies = load_json(MOVIE_FILE)
    genre_filter = request.args.get("genre")
    rating_filter = request.args.get("rating")
    
    # Filter by genre
    if genre_filter:
        movies = [m for m in movies if m["genre"].lower() == genre_filter.lower()]
    # Filter by rating (>= selected)
    if rating_filter:
        movies = [m for m in movies if float(m["rating"]) >= float(rating_filter)]
    
    return render_template("index.html", movies=movies)

# Add new movie
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    if request.method == "POST":
        title = request.form.get("title").strip()
        genre = request.form.get("genre").strip()
        rating = request.form.get("rating").strip()
        review = request.form.get("review").strip()
        description = request.form.get("description", "").strip()
        photo = request.files.get("photo")
        filename = ""

        # Validate inputs
        if not title or not genre or not rating:
            flash("Title, genre, and rating are required!", "error")
            return redirect(request.url)

        # Handle photo upload
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        movies = load_json(MOVIE_FILE)
        # Check for duplicate title
        if any(m["title"].lower() == title.lower() for m in movies):
            flash("Movie with this title already exists!", "error")
            return redirect(request.url)

        movies.append({
            "title": title,
            "genre": genre,
            "rating": rating,
            "review": review,
            "description": description,
            "photo": filename
        })
        save_json(MOVIE_FILE, movies)
        flash(f"{title} added successfully!", "success")
        return redirect(url_for("index"))

    return render_template("add_movie.html")

# Edit existing movie
@app.route("/edit/<string:title>", methods=["GET", "POST"])
def edit_movie(title):
    movies = load_json(MOVIE_FILE)
    movie = next((m for m in movies if m["title"] == title), None)
    if not movie:
        flash("Movie not found!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        new_title = request.form.get("title").strip()
        genre = request.form.get("genre").strip()
        rating = request.form.get("rating").strip()
        review = request.form.get("review").strip()
        description = request.form.get("description", "").strip()
        photo = request.files.get("photo")

        if not new_title or not genre or not rating:
            flash("Title, genre, and rating are required!", "error")
            return redirect(request.url)

        # Update photo if uploaded
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            movie["photo"] = filename

        movie.update({
            "title": new_title,
            "genre": genre,
            "rating": rating,
            "review": review,
            "description": description
        })

        save_json(MOVIE_FILE, movies)
        flash(f"{new_title} updated successfully!", "success")
        return redirect(url_for("index"))

    return render_template("edit_movie.html", movie=movie)

# Delete movie
@app.route("/delete/<string:title>")
def delete_movie(title):
    movies = load_json(MOVIE_FILE)
    movies = [m for m in movies if m["title"] != title]
    save_json(MOVIE_FILE, movies)
    flash(f"{title} deleted successfully!", "success")
    return redirect(url_for("index"))

# Movie details
@app.route("/movie/<string:title>")
def movie_details(title):
    movies = load_json(MOVIE_FILE)
    movie = next((m for m in movies if m["title"] == title), None)
    if not movie:
        flash("Movie not found!", "error")
        return redirect(url_for("index"))
    return render_template("movie_details.html", movie=movie)

# Metrics page
@app.route("/metrics")
def metrics():
    movies = load_json(MOVIE_FILE)
    genre_avg = {}
    genre_count = {}
    for m in movies:
        g = m["genre"]
        genre_count[g] = genre_count.get(g, 0) + 1
        genre_avg[g] = genre_avg.get(g, 0) + float(m["rating"])
    
    genre_avg = {g: round(genre_avg[g]/genre_count[g], 2) for g in genre_avg}
    most_watched = max(genre_count, key=genre_count.get) if genre_count else "N/A"
    top_rated = max(movies, key=lambda x: float(x["rating"]))["title"] if movies else "N/A"
    
    return render_template("metrics.html", genre_avg=genre_avg, most_watched=most_watched, top_rated=top_rated)

# ---------------------
# Run the app
# ---------------------
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
