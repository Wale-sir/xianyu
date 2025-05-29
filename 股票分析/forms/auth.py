from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次输入的密码不一致')
    ])

class ProfileForm(FlaskForm):
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址')
    ])
    bio = TextAreaField('个人简介', validators=[Optional()])
    password = PasswordField('新密码', validators=[Optional()])
    confirm_password = PasswordField('确认新密码', validators=[
        Optional(),
        EqualTo('password', message='两次输入的密码不一致')
    ]) 