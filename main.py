import math

from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import os
from werkzeug.utils import secure_filename

with open("config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.secret_key = 'the-random-string'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)
if (local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(120), nullable=False)

class Users(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80),nullable=False)
    name = db.Column(db.String(80),nullable=False)
    password = db.Column(db.String(80), nullable=False)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * params['no_of_posts']:(page - 1) * params['no_of_posts'] + params['no_of_posts']]
    if (page == 1):
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif (page == last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template("index.html", params=params, posts=posts, prev=prev, next=next)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    #old code
    # if 'user' in session and session['user'] == params['admin_user']:
    if 'u' in session and session['u'] == params['admin_user']:
        if (request.method == "POST"):
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')

            # my code
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            img_file = f.filename
            # my code ends

            # img_file = request.form.get('img_file')
            date = datetime.now()
            if (sno == '0'):
                post = Posts(title=box_title, tagline=tline, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)


#my code
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        uemail = request.form.get('uemail')
        uname = request.form.get('uname')
        upass = request.form.get('upass')
        user = Users(email=uemail,name=uname,password=upass)
        db.session.add(user)
        db.session.commit()
        return render_template("login.html", params=params)
    return render_template("register.html",params=params)



@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():


    #old Code
    # if 'user' in session and session['user'] == params['admin_user']:
    if 'u' in session and session['u'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    # my code
    users = Users.query.all()
    for user in users:
        if 'u' in session and session['u'] == user.email:
            user_d = Users.query.filter_by(email=session['u'])
            posts = Posts.query.all()
            return render_template("user_dashboard.html", params=params, posts=posts, user_d=user_d)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('pass')


        #old code
        if (username == params['admin_user'] and userpass == params['admin_password']):
            # session['user'] = username
            session['u'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

            # else:
            #     return render_template("login.html", params=params)

        # my code
        else:
            users = Users.query.all()
            for user in users:
                if (username == user.email and userpass == user.password):
                    session['u'] = username
                    posts = Posts.query.all()
                    user_d = Users.query.filter_by(email=session['u'])
                    return render_template("user_dashboard.html", params=params, posts=posts,user=user,user_d=user_d)
    return render_template("login.html", params=params)



@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    #old code
    # if 'user' in session and session['user'] == params['admin_user']:
    if 'u' in session and session['u'] == params['admin_user']:

        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return 'updated successfully'


@app.route("/logout")
def logout():
    #old code
    # if 'user' in session:
    #     session.pop('user')

    #my code
    if 'u' in session:
        session.pop('u')
    return redirect('/dashboard')


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + '\n' + phone
                          )

    return render_template("contact.html", params=params)


app.run(debug="True")
