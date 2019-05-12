from flask import Flask, g, render_template, flash, redirect, url_for
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import (LoginManager, current_user,
                         login_user, login_required, logout_user)

import forms
import models
from slugify import slugify


DEBUG = True
HOST = "127.0.0.1"
PORT = 8000

app = Flask(__name__)
app.secret_key = "fdzopkdeopznfrioencoke"


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route("/")
@app.route("/entries")
def entries():
    entries = models.Entry.select().where(
        models.Entry.user == g.user._get_current_object()
        ).order_by(
        models.Entry.date.desc()
        )
    return render_template("index.html", entries=entries)


@app.route("/filter/<string:tagname>")
@login_required
def filter(tagname):
    entries = models.Entry.select().where(
        models.Entry.user == g.user._get_current_object(),
        models.Entry.tagfield.contains(tagname)
        ).order_by(
        models.Entry.date.desc()
        )
    return render_template("index.html", entries=entries)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        models.User.create(first_name=form.first_name.data,
                           email=form.email.data,
                           password=generate_password_hash(
                             form.password1.data))
        user = models.User.get(models.User.email == form.email.data)
        login_user(user)
        flash("You are registered!", "success")
        return redirect(url_for("entries"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("No such email adress in our database", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Welcome to your Journal, " +
                      user.first_name +
                      "!", "success")
                return redirect(url_for('entries'))
            else:
                flash("Password do not match our record", "error")
                return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("See you soon!")
    return redirect(url_for("entries"))


@app.route("/entries/new", methods=("GET", "POST"))
@login_required
def new_entry():
    form = forms.EntryForm()
    if form.validate_on_submit():
        # testing if prospective slug unique before creating new entry
        if models.Entry.test_slug_outstanding(
          slugify(form.title.data.strip())):
            flash("Entry '" +
                  form.title.data.strip() +
                  "' already exists. Cant create entry.", "error")
            return redirect(url_for("entries"))
        else:
            models.Entry.create(user=g.user._get_current_object(),
                                title=form.title.data.strip(),
                                date=form.date.data,
                                time_spent=form.time_spent.data,
                                material=form.material.data.strip(),
                                resource=form.resource.data.strip(),
                                tagfield=form.tagfield.data,
                                slug=slugify(form.title.data.strip()))
            # for each tag, either creating and adding entry or,
            # if tag outstanding, just adding entry
            if form.tagfield.data:
                for each in form.tagfield.data.split(","):
                    try:
                        existing_tag = models.Tag.get(
                            models.Tag.name == each.strip().lower())
                        existing_tag.entries.add(models.Entry.get(
                            models.Entry.title == form.title.data.strip()))
                    except models.Tag.DoesNotExist:
                        new_tag = models.Tag.create(name=each.strip().lower())
                        new_tag.entries.add(models.Entry.get(
                            models.Entry.title == form.title.data.strip()))
            flash("Entry saved!", "success")
            return redirect(url_for("entries"))
    return render_template("new.html", form=form)


@app.route("/entries/<string:slug>", methods=["GET", "POST"])
# login required so that seeing, deleting and editing
# restricted to user of the entry
@login_required
def detail(slug):
    try:
        detail = models.Entry.select().where(models.Entry.slug == slug).get()
    except models.Entry.DoesNotExist:
        flash("Sorry, '" +
              slug +
              "' entry does not exists")
        return redirect(url_for("entries"))
    if current_user == detail.user:
        return render_template("detail.html", detail=detail)
    else:
        flash("Sorry, " +
              current_user.first_name +
              ". This entry is not yours to see")
        return redirect(url_for("entries"))


@app.route("/entries/<string:slug>/delete", methods=["GET", "POST"])
@login_required
def delete(slug):
    detail = models.Entry.select().where(models.Entry.slug == slug).get()
    if current_user == detail.user:
        # removing entry for each tag associated
        for each in detail.tagfield.split(","):
            related_tag = models.Tag.get(
                models.Tag.name == each.strip().lower())
            related_tag.entries.remove(detail)
        detail.delete_instance()
        flash("Entry deleted!", "success")
        return redirect(url_for("entries"))
    else:
        flash("Sorry, " +
              current_user.first_name +
              ". This entry is not yours to delete")
        return redirect(url_for("entries"))


@app.route("/entries/<string:slug>/edit", methods=["GET", "POST"])
# login required so that deleting and editing
@login_required
def edit(slug):
    entry = models.Entry.select().where(models.Entry.slug == slug).get()
    if current_user == entry.user:
        form = forms.EntryForm(obj=entry)
        if form.validate_on_submit():
            if (models.Entry.test_slug_outstanding(
                    slugify(form.title.data.strip())) and
                    entry.slug != slugify(form.title.data.strip())):
                flash("Entry '" +
                      form.title.data.strip() +
                      "' already exists. Cant edit entry.", "error")
                return redirect(url_for("entries"))
            else:
                # if there are tags, the entry needs to be removed from them
                if entry.tagfield:
                    for each in entry.tagfield.split(","):
                        related_tag = models.Tag.get(
                            models.Tag.name == each.strip().lower())
                        related_tag.entries.remove(entry)
                entry.delete_instance()
                # creation of a new entry, along with eventual new tags
                models.Entry.create(user=g.user._get_current_object(),
                                    title=form.title.data.strip(),
                                    date=form.date.data,
                                    time_spent=form.time_spent.data,
                                    material=form.material.data.strip(),
                                    resource=form.resource.data.strip(),
                                    tagfield=form.tagfield.data,
                                    slug=slugify(form.title.data.strip()))
                if form.tagfield.data:
                    for each in form.tagfield.data.split(","):
                        try:
                            # if tag already exists, just add the entry
                            existing_tag = models.Tag.get(
                                models.Tag.name == each.strip().lower())
                            existing_tag.entries.add(models.Entry.get(
                                models.Entry.title == form.title.data.strip()))
                        except models.Tag.DoesNotExist:
                            new_tag = models.Tag.create(
                                name=each.strip().lower())
                            new_tag.entries.add(models.Entry.get(
                                models.Entry.title == form.title.data.strip()))
                flash("Entry edited!", "success")
                return redirect(url_for("entries"))
        return render_template("edit.html", form=form)
    else:
        flash("Sorry, " +
              current_user.first_name +
              ". This entry is not yours to edit")
        return redirect(url_for("entries"))


if __name__ == "__main__":
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)
