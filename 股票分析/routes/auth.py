from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from forms.auth import LoginForm, RegisterForm, ProfileForm
import logging
from extensions import csrf

# 创建模块级别的logger
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('stock.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('stock.index'))
        flash('用户名或密码错误', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf.exempt  # 临时禁用 CSRF 保护用于调试
def register():
    logger.info('---- Entering register route ----')
    logger.info('Register route accessed')
    if current_user.is_authenticated:
        logger.info('User already authenticated, redirecting to index')
        return redirect(url_for('stock.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        logger.info('Registration form validated successfully')
        username = form.username.data

        if User.get_by_username(username):
            logger.warning(f'Username {username} already exists')
            flash('用户名已存在', 'danger')
            return render_template('auth/register.html', form=form)
        
        user_data = {
            'username': username,
            'password': form.password.data,
        }
        
        logger.info(f'Attempting to create user: {username}')
        user = User.create(**user_data)
        
        if user:
            logger.info(f'User {username} created successfully. Attempting to log in.')
            login_user(user)
            logger.info(f'User {username} logged in successfully')
            flash('注册成功！', 'success')
            return redirect(url_for('stock.index'))
        else:
            logger.error(f'Failed to create user: {username}. User.create returned None.')
            flash('注册失败，请稍后重试', 'danger')
            return render_template('auth/register.html', form=form)

    else:
        logger.warning('Registration form validation failed')
        logger.warning(f'Form errors: {form.errors}')

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已退出登录', 'info')
    return redirect(url_for('stock.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.update({
            'bio': form.bio.data
        })
        
        if form.password.data:
            current_user.update({
                'password': generate_password_hash(form.password.data)
            })
        
        flash('个人资料已更新', 'success')
        return redirect(url_for('auth.profile'))
    
    if request.method == 'GET':
        form.bio.data = current_user.bio
    
    return render_template('auth/profile.html', form=form) 