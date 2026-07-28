from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = "taskflow_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Import models
from models.user import User
from models.task import Task


@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.", "danger")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user"] = user.username

            flash("Welcome back!", "success")
            return redirect("/dashboard")

        flash("Invalid username or password.", "danger")
        return redirect("/login")

    return render_template("login.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    current_user = User.query.filter_by(username=session["user"]).first()

    tasks = Task.query.filter_by(user_id=current_user.id).all()

    total_tasks = len(tasks)
    completed_tasks = Task.query.filter_by(status="Completed").count()
    pending_tasks = Task.query.filter_by(status="Pending").count()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )


# ---------------- ADD TASK ---------------- #

@app.route("/add-task", methods=["GET", "POST"])
def add_task():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        current_user = User.query.filter_by(username=session["user"]).first()

        task = Task(
            title=title,
            description=description,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_task.html")


# ---------------- EDIT TASK ---------------- #

@app.route("/edit-task/<int:id>", methods=["GET", "POST"])
def edit_task(id):

    if "user" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if request.method == "POST":

        task.title = request.form["title"]
        task.description = request.form["description"]

        db.session.commit()

        flash("Task updated successfully.", "success")
        return redirect("/dashboard")

    return render_template("edit_task.html", task=task)


# ---------------- DELETE TASK ---------------- #

@app.route("/delete-task/<int:id>")
def delete_task(id):

    if "user" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted successfully.", "success")

    return redirect("/dashboard")


# ---------------- COMPLETE TASK ---------------- #

@app.route("/complete-task/<int:id>")
def complete_task(id):

    if "user" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    task.status = "Completed"

    db.session.commit()

    flash("Task marked as completed.", "success")

    return redirect("/dashboard")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.pop("user", None)

    flash("You have been logged out.", "success")

    return redirect("/")


# ---------------- DATABASE ---------------- #

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)