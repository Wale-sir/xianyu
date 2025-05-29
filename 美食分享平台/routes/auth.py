from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.relationship import Relationship
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('food.index'))
        flash('用户名或密码错误')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('auth.register'))
        
        if User.get_by_username(username):
            flash('用户名已存在')
            return redirect(url_for('auth.register'))
        
        user = User.create(username, password)
        if user:
            login_user(user)
            return redirect(url_for('food.index'))
        flash('注册失败，请重试')
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('food.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@auth_bp.route('/profile/<user_id>', methods=['GET'])
@login_required
def profile(user_id=None):
    if user_id is None:
        profile_user = current_user
    else:
        profile_user = User.get_by_id(user_id)
        if not profile_user:
            flash('用户不存在')
            return redirect(url_for('food.index'))
    
    # 使用用户表中的计数
    following_count = profile_user.following_count
    followers_count = profile_user.followers_count
    is_following = Relationship.is_following(current_user.id, profile_user.id) if profile_user.id != current_user.id else False
    
    # 获取关注列表和粉丝列表
    following = Relationship.get_following(profile_user.id)
    followers = Relationship.get_followers(profile_user.id)
    
    if request.method == 'POST' and user_id is None:
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 检查当前密码是否正确
        if current_password and not current_user.check_password(current_password):
            flash('当前密码错误')
            return redirect(url_for('auth.profile'))
        
        # 更新用户名
        if username != current_user.username:
            if User.get_by_username(username):
                flash('用户名已存在')
                return redirect(url_for('auth.profile'))
            current_user.update_profile({'username': username})
        
        # 更新密码
        if new_password:
            if new_password != confirm_password:
                flash('两次输入的新密码不一致')
                return redirect(url_for('auth.profile'))
            current_user.update_password(new_password)
        
        flash('个人资料更新成功')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html',
                         profile_user=profile_user,
                         following_count=following_count,
                         followers_count=followers_count,
                         is_following=is_following,
                         following=following,
                         followers=followers) 