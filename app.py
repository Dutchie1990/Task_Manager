import os
from flask_pymongo import PyMongo
from flask import (Flask, flash, render_template,
                redirect, request, session, url_for)
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in the db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put user into session
        session["user"] = request.form.get("username").lower()
        flash("Registration succesfull")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username already exists in the db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure the hashed password matches
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))
            else:
                # invalid password
                flash("Username and/or password are incorrect")
                return redirect(url_for("login"))
        else:
            # username doesnt exists
            flash("Username and/or password are incorrect")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    try:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        if session["user"]:
            return render_template("profile.html", username=username)
    except KeyError:
        return redirect(url_for('login'))


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for('login'))


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        try:
            is_urgent = "on" if request.form.get("is_urgent") else "off"
            task = {
                "category_name": request.form.get("category_name"),
                "task_name": request.form.get("task_name"),
                "task_description": request.form.get("task_description"),
                "is_urgent": is_urgent,
                "due_date": request.form.get("due_date"),
                "created_by": session["user"]
            }
            mongo.db.tasks.insert_one(task)
            flash("Insert succesfull")
            return redirect(url_for("get_tasks"))
        except KeyError:
            flash("Insert failed")

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if request.method == "POST":
        try:
            is_urgent = "on" if request.form.get("is_urgent") else "off"
            updated_task = {
                "category_name": request.form.get("category_name"),
                "task_name": request.form.get("task_name"),
                "task_description": request.form.get("task_description"),
                "is_urgent": is_urgent,
                "due_date": request.form.get("due_date"),
                "created_by": session["user"]
            }
            mongo.db.tasks.update({"_id": ObjectId(task_id)}, updated_task)
            flash("Update succesfull")
        except KeyError:
            flash("Insert failed")

    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_task.html", task=task, categories=categories)


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    mongo.db.tasks.remove({"_id": ObjectId(task_id)})
    flash("Task succesfully deleted")
    return redirect(url_for('get_tasks'))


@app.route("/manage_categories")
def manage_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template('categories.html', categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("Category is added succesfully")
        return redirect(url_for('manage_categories'))

    return render_template("add_categories.html")


@app.route('/edit_category/<category_id>', methods=["POST", "GET"])
def edit_category(category_id):
    if request.method == "POST":
        updated_category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(
                category_id)}, updated_category)
        flash("Category updated")
        return redirect(url_for('manage_categories'))
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("category succesfully deleted")
    return redirect(url_for('manage_categories'))


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.tasks.find({"$text": {"$search": query}}))
    return render_template("tasks.html", tasks=tasks)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
