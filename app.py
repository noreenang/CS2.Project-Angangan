from flask import Flask, render_template, request, redirect, session, url_for
import json, os

app = Flask(__name__)
app.secret_key = "secret"

# ---------- Files ----------
USERS_FILE = "users.json"
MOVIES_FILE = "movies.json"

# ---------- Setup ----------
def init_files():
    """Create JSON files if they don't exist."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({"users": []}, f, indent=4)

    if not os.path.exists(MOVIES_FILE):
        with open(MOVIES_FILE, "w") as f:
            json.dump({"movies": []}, f, indent=4)

def load(file):
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def next_id(movies):
    """Generate next unique ID for movies."""
    return max([m["id"] for m in movies], default=0) + 1

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load(USERS_FILE)["users"]
        username = request.form["username"]
        password = request.form["password"]
        for u in users:
            if u["username"] == username and u["password"] == password:
                session["user"] = username
                return redirect("/dashboard")
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if not username or not password:
            return render_template("register.html", error="All fields are required")
        data = load(USERS_FILE)
        # Check if username exists
        if any(u["username"] == username for u in data["users"]):
            return render_template("register.html", error="Username already taken")
        data["users"].append({"username": username, "password": password})
        save(USERS_FILE, data)
        return redirect("/")
    return render_template("register.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    movies = load(MOVIES_FILE)["movies"]
    return render_template("dashboard.html", movies=movies, user=session["user"])

# ---------- ADD MOVIE ----------
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    if "user" not in session:
        return redirect("/")
    if request.method == "POST":
        title = request.form.get("title")
        genre = request.form.get("genre")
        review = request.form.get("review")
        poster = request.form.get("poster", "")
        try:
            rating = int(request.form.get("rating", 0))
            if rating < 1 or rating > 10:
                raise ValueError
        except ValueError:
            return render_template("add_movie.html", error="Rating must be 1-10")
        if not title or not genre:
            return render_template("add_movie.html", error="Title and genre are required")

        data = load(MOVIES_FILE)
        data["movies"].append({
            "id": next_id(data["movies"]),
            "title": title,
            "genre": genre,
            "rating": rating,
            "review": review,
            "poster": poster
        })
        save(MOVIES_FILE, data)
        return redirect("/dashboard")
    return render_template("add_movie.html")

# ---------- DELETE MOVIE ----------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/")
    data = load(MOVIES_FILE)
    data["movies"] = [m for m in data["movies"] if m["id"] != id]
    save(MOVIES_FILE, data)
    return redirect("/dashboard")

# ---------- STATS ----------
@app.route("/stats")
def stats():
    if "user" not in session:
        return redirect("/")
    movies = load(MOVIES_FILE)["movies"]

    genres = {}
    for m in movies:
        genres.setdefault(m["genre"], []).append(m["rating"])

    avg = {g: round(sum(r)/len(r), 2) for g, r in genres.items()}
    most = max(genres, key=lambda g: len(genres[g]), default=None)
    top = max(movies, key=lambda m: m["rating"], default=None)

    return render_template("stats.html", avg=avg, most=most, top=top)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    init_files()  # Make sure JSON files exist before running
    app.run(debug=True)
