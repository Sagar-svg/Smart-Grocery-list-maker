from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db , bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, GroceryForm, GlistnameForm
from flaskblog.models import User, Grocerylist, Grocery
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os


# this stores the temporary grocery items of list
grclist = {"name":[], "quantity":[], "measure":[]}




@app.route("/")
@app.route("/home")
def home():
    glist = Grocerylist.query.all()
    return render_template('home.html', glist = glist)


@app.route("/about", methods = ['GET', 'POST'])
@login_required #ensures that the current user is logged in
def about():
    glist = Grocerylist.query.all()
    form =GroceryForm()
    forml = GlistnameForm()
    if request.method == 'GET':
        list = zip(grclist["name"], grclist["quantity"], grclist["measure"])
        
        # render_template can take list(present temporary grocery), glist(grocerylist present in the database)
        return render_template('about.html', title='New list',form = form,forml = forml, list = list, glist = glist)
    
    if form.validate_on_submit():
        if form.Groceryname.data in grclist["name"]:
            for index, _ in enumerate(grclist["name"]):
                #check for if the grocery want to be added is already present and if present just increament quantity
                if _ == form.Groceryname.data:
                    grclist["quantity"][index] = str(int(grclist["quantity"][index].strip()) + int(form.quantity.data.strip()))
                    break
        else:
            #appends to temporary list
            grclist["name"].append(form.Groceryname.data)
            grclist["quantity"].append(form.quantity.data)
            grclist["measure"].append(form.measure.data)
        
    else:
        #if the input is invalid
        flash(f'Please enter appropriate input', 'danger')

    return redirect(url_for('about'))

@app.route("/remove", methods = ['POST'])
@login_required
def remove():
    form = GroceryForm()
    postData = request.form['name_to_delete']
    print(postData)
    for i, _ in enumerate(grclist['name']):
        if _ == postData:
            grclist["name"].remove(postData)
            grclist["quantity"] = grclist["quantity"][:i]+grclist["quantity"][i+1:]
            grclist["measure"] = grclist["measure"][:i]+grclist["measure"][i+1:]
            print('removed', grclist["name"])
            break
    
    return redirect(url_for('about'))


@app.route("/delete/<int:list_id>", methods = ['POST'])
@login_required
def delete(list_id):
    list = Grocerylist.query.get_or_404(list_id)
    if list.owner != current_user:
        abort(403)

    db.session.delete(list)
    db.session.commit()
    flash(f'Your list has been deleted', 'success')
    return(redirect(url_for('home')))


@app.route("/add", methods = ['GET', 'POST'])
@login_required
def add(): 
    global grclist
    # before adding list to database check for valid name
    forml = GlistnameForm()
    if not forml.Glistname.data:
        flash(f'Please enter appropriate list name', 'danger')
        return redirect(url_for('about'))
    #check for the unique list name
    if forml.Glistname.data.strip() in [grlst.title for grlst in Grocerylist.query.all()]:
        flash(f'Name already taken, Please use other name', 'danger')
        return redirect(url_for('about'))
    list = Grocerylist(title = forml.Glistname.data.strip(), owner = current_user)
    db.session.add(list)
    db.session.commit()
    for grocery in zip(grclist['name'], grclist['quantity'], grclist['measure']):
        db.session.add(Grocery(name = grocery[0], quantity = int(grocery[1]), measure = grocery[2], listname = list))

    
    db.session.commit()
    #emptying the temporary list
    grclist = {"name":[], "quantity":[], "measure":[]}
    
    return redirect(url_for('about'))


@app.route("/readd", methods = ['GET', 'POST'])
@login_required
def readd():
    global grclist
    ingred = [ing.strip() for ing in request.form['ingredients'].split(",")]
    for ing in ingred:
        if ing not in grclist['name']:
            grclist["name"].append(ing)
            grclist["quantity"].append("1")
            grclist["measure"].append("")
    return redirect(url_for('about'))

@app.route("/suggest", methods = ['GET','POST'])
@login_required
def suggest():
    global grclist
    form = GroceryForm()
#the grocery present in the list must be atleast 4 or greater the 4
    grocery = grclist['name']
    if len(grocery) <= 3:
        flash(f'Please select more groceries in your list.', 'danger')
        return redirect(url_for('about'))
    rdata = pd.read_csv("C:/Users/SAGAR THASAL/wrapper/projects/flask_blog/flaskblog/static/rDataReq")

# Ml logic
    lst = np.array(rdata['ingredients'].append(pd.Series(str(grocery[1:-1]))))
    lst = lst.tolist()
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(lst)
    feature_names = vectorizer.get_feature_names()
    dense = vectors.todense()
    denselist = dense.tolist()
    df = pd.DataFrame(denselist, columns = feature_names)
    x = cosine_similarity(vectors, vectors)
    x = np.asarray(x, dtype = 'float64')
    newdata = rdata
    newdata['simmilarity'] = x[-1][:len(x[-1])-1]
    newdata = newdata.sort_values(by = ['simmilarity'])

#Take the last 5 suggestion as the list was sorted in Ascending order
    list = zip(grclist["name"], grclist["quantity"], grclist["measure"])
    rlist =  zip(newdata[-1:-6:-1]['title'], newdata[-1:-6:-1]['ingredients'], newdata[-1:-6:-1]['url'])
    glist = Grocerylist.query.all()
    forml = GlistnameForm()
    return render_template('about.html', title='About',form = form,list = list, forml = forml,  glist = glist, rlist = rlist)

@app.route("/view/<list_id>", methods = ['GET', 'POST'])
@login_required
def view(list_id):
    glist = Grocerylist.query.all()
    list = Grocerylist.query.get_or_404(list_id)
    grc = Grocery.query.filter_by(grocery_id = list.id)
    return render_template('view.html', list = list, grc = grc, glist = glist)

@app.route("/list/<list_id>/update", methods = ['GET', 'POST'])
@login_required
def update(list_id):
    global grclist
    form =GroceryForm()
    forml = GlistnameForm()
    list_ = Grocerylist.query.get_or_404(list_id)
    glist = Grocerylist.query.all()
    grc = Grocery.query.filter_by(grocery_id = list_.id)
    for gr in grc:
        grclist["name"].append(gr.name)
        grclist["quantity"].append(gr.quantity)
        grclist["measure"].append(gr.measure)
    list = zip(grclist["name"], grclist["quantity"], grclist["measure"])
    forml.Glistname.data = list_.title
    return render_template('about.html', title='Update list',form = form,forml = forml, list = list, glist = glist, legend = "update")


@app.route("/register", methods=['GET', 'POST'])
def register():
    #check if already login
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        #to store the hashed password in database
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your Account has been created for, You can log in!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        #gets the user of that email
        user = User.query.filter_by(email = form.email.data).first()
        #the password is hashed so cannot be directly compared 
        #for this we use check_password_hash(hased_pass, entered_password)
        if user and bcrypt.check_password_hash(user.password, form.password.data):#checks if user exit and checks password is valid
            login_user(user, remember = form.remember.data)#login the user
            #if redirected from another page it has to be resend there
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/account")
@login_required
def account():
    
    return render_template('account.html', title='Account')
    
    
