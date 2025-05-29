from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, FloatField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=20)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])

class FoodForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(max=100)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired()
    ])
    price = FloatField('Price', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    rating = FloatField('Rating', validators=[
        NumberRange(min=0, max=5)
    ])
    tags = StringField('Tags (comma separated)')
    longitude = StringField('Longitude')
    latitude = StringField('Latitude')
    images = FileField('Images', render_kw={'multiple': True})

class ReviewForm(FlaskForm):
    rating = FloatField('Rating', validators=[
        DataRequired(),
        NumberRange(min=0, max=5)
    ])
    comment = TextAreaField('Comment', validators=[
        DataRequired(),
        Length(max=500)
    ]) 