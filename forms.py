from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flaskblog.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user:
            raise ValidationError("Username Already Taken :(")
    def validate_email(self, email):
        user = User.query.filter_by(email = email.data).first()
        if user:
            raise ValidationError("Email Already Taken :(")




class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class GroceryForm(FlaskForm):
    Groceryname = StringField('Groceryname',
                           validators=[DataRequired(), Length(min=2, max=20)])
    quantity = StringField('quantity', validators=[DataRequired(), Length(min = 1, max = 6)])
    measure = StringField('measure', validators = [Length(min = 0, max = 3)])
    submit = SubmitField('Add')

class GlistnameForm(FlaskForm):
    Glistname = StringField('Glistname',
                           validators=[DataRequired(), Length(min=2, max=20)])

    submit = SubmitField('Add')
