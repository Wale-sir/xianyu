from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.share import Share
from models.user import User
import os
from werkzeug.utils import secure_filename
from datetime import datetime

share_bp = Blueprint('share', __name__)

# 配置文件上传
UPLOAD_FOLDER = 'static/uploads/shares'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@share_bp.route('/shares')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    shares = Share.get_all_shares(limit=per_page, skip=skip)
    return render_template('share/index.html', shares=shares, page=page)

@share_bp.route('/shares/create', methods=['POST'])
@login_required
def create():
    title = request.form.get('title')
    content = request.form.get('content')
    images = []
    
    # 处理图片上传
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                images.append(f"uploads/shares/{filename}")
    
    share_data = {
        'user_id': current_user.id,
        'title': title,
        'content': content,
        'images': images
    }
    
    share = Share.create(share_data)
    flash('分享发布成功', 'success')
    return redirect(url_for('share.index'))

@share_bp.route('/shares/<share_id>/edit', methods=['POST'])
@login_required
def edit(share_id):
    share = Share.get_by_id(share_id)
    if not share:
        flash('分享不存在', 'danger')
        return redirect(url_for('share.index'))
    
    if share.user_id != current_user.id:
        flash('您没有权限编辑此分享', 'danger')
        return redirect(url_for('share.index'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    images = share.images
    
    # 处理图片上传
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                images.append(f"uploads/shares/{filename}")
    
    share_data = {
        'title': title,
        'content': content,
        'images': images
    }
    
    share.update(share_data)
    flash('分享更新成功', 'success')
    return redirect(url_for('share.index'))

@share_bp.route('/shares/<share_id>/delete', methods=['POST'])
@login_required
def delete(share_id):
    share = Share.get_by_id(share_id)
    if not share:
        flash('分享不存在', 'danger')
        return redirect(url_for('share.index'))
    
    if share.user_id != current_user.id:
        flash('您没有权限删除此分享', 'danger')
        return redirect(url_for('share.index'))
    
    # 删除相关图片
    for image in share.images:
        image_path = os.path.join('static', image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    share.delete()
    flash('分享删除成功', 'success')
    return redirect(url_for('share.index'))

@share_bp.route('/shares/<share_id>/like', methods=['POST'])
@login_required
def like(share_id):
    share = Share.get_by_id(share_id)
    if not share:
        return jsonify({'error': '分享不存在'}), 404
    
    share.add_like()
    return jsonify({'likes': share.likes})

@share_bp.route('/shares/<share_id>/comment', methods=['POST'])
@login_required
def comment(share_id):
    share = Share.get_by_id(share_id)
    if not share:
        return jsonify({'error': '分享不存在'}), 404
    
    content = request.form.get('content')
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400
    
    share.add_comment(current_user.id, content)
    return jsonify({'success': True}) 