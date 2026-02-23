from flask import Flask, render_template, request, redirect, url_for, flash, session
import json, os

from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "secret_key_here"

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"

# --- JSON Helpers ---
def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# --- Utility for auto ID ---
def get_next_movie_id(movies):
    if not movies:
        return 1
    return max(m['id'] for m in movies) + 1

# --- Routes ---
@app.route("/")
def index():
    movies = load_json(MOVIES_FILE)
    return render_template("index.html", movies=movies, user=session.get("username"))

# --- Authentication ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_json(USERS_FILE)
        username = request.form["username"]
        password = request.form["password"]

        for user in users:
            if user["username"] == username and user["password"] == password:
                session["username"] = username  # store username in session
                flash(f"Login successful! Welcome, {username}!")
                return redirect(url_for("index"))

        flash("Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)  # remove user from session
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        users = load_json(USERS_FILE)

        # --- Basic validation ---
        if not username or not password:
            flash("Username and password cannot be empty")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("register"))

        if any(u["username"] == username for u in users):
            flash("Username already exists")
            return redirect(url_for("register"))

        # --- Save user only after validation passes ---
        users.append({"username": username, "password": password})
        save_json(USERS_FILE, users)

        flash("Registered successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")
    
# --- Movie CRUD ---
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    if "username" not in session:
        flash("Please login to add movies.")
        return redirect(url_for("login"))

    if request.method == "POST":
        movies = load_json(MOVIES_FILE)

        try:
            rating = float(request.form.get("rating", 0))
        except ValueError:
            rating = 0

        # --- HANDLE IMAGE ---
        image_file = request.files.get("image")
        filename = ""

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

        movie = {
            "id": get_next_movie_id(movies),
            "title": request.form.get("title", "").strip(),
            "genre": request.form.get("genre", "").strip(),
            "rating": rating,
            "review": request.form.get("review", "").strip(),
            "description": request.form.get("description", "").strip(),
            "image": filename,
            "owner": session["username"]
        }

        movies.append(movie)
        save_json(MOVIES_FILE, movies)
        flash(f'Movie "{movie["title"]}" added!')
        return redirect(url_for("index"))

    return render_template("add_movie.html")


@app.route("/movie/<int:id>")
def movie_details(id):
    movies = load_json(MOVIES_FILE)
    movie = next((m for m in movies if m["id"] == id), None)
    if not movie:
        flash("Movie not found")
        return redirect(url_for("index"))
    return render_template("movie_details.html", movie=movie, user=session.get("username"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_movie(id):
    if "username" not in session:
        flash("Please login to edit movies.")
        return redirect(url_for("login"))

    movies = load_json(MOVIES_FILE)
    movie = next((m for m in movies if m["id"] == id), None)

    if not movie:
        flash("Movie not found")
        return redirect(url_for("index"))

    if movie.get("owner") != session["username"]:
        flash("You cannot edit someone else's movie.")
        return redirect(url_for("index"))



    if request.method == "POST":
        movie["title"] = request.form.get("title", "").strip()
        movie["genre"] = request.form.get("genre", "").strip()

        try:
            movie["rating"] = float(request.form.get("rating", 0))
        except ValueError:
            movie["rating"] = 0

        movie["review"] = request.form.get("review", "").strip()
        movie["description"] = request.form.get("description", "").strip()

        # --- HANDLE IMAGE UPDATE ---
        image_file = request.files.get("image")

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            movie["image"] = filename

        save_json(MOVIES_FILE, movies)
        flash("Movie updated!")
        return redirect(url_for("movie_details", id=id))

    return render_template("edit_movie.html", movie=movie)

@app.route("/delete/<int:id>")
def delete_movie(id):
    if "username" not in session:
        flash("Please login to delete movies.")
        return redirect(url_for("login"))

    movies = load_json(MOVIES_FILE)
    movie = next((m for m in movies if m["id"] == id), None)

    if not movie:
        flash("Movie not found")
        return redirect(url_for("index"))

    # 🔥 OWNER CHECK
    if movie.get("owner") != session["username"]:
       flash("You cannot delete someone else's movie.")
       return redirect(url_for("index"))


    # Delete movie
    movies = [m for m in movies if m["id"] != id]
    save_json(MOVIES_FILE, movies)

    flash(f'Movie "{movie["title"]}" deleted!')
    return redirect(url_for("index"))

    

# ======================
if __name__ == "__main__":
    app.run(debug=True)
