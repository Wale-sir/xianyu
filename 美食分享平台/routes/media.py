from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required
from extensions import mongo
from gridfs import GridFS
from bson.objectid import ObjectId
from PIL import Image
import io

media_bp = Blueprint('media', __name__)
fs = GridFS(mongo.db)

@media_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # 如果是图片，进行压缩
        if file.content_type.startswith('image/'):
            img = Image.open(file)
            # 调整图片大小
            img.thumbnail((800, 800))
            # 转换为JPEG格式
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            # 保存到内存
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=85)
            img_io.seek(0)
            file = img_io
        
        file_id = fs.put(
            file,
            filename=file.filename,
            content_type=file.content_type
        )
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': str(file_id)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/<file_id>')
def get_file(file_id):
    try:
        print(f"Attempting to get file with ID: {file_id}")
        # 检查文件是否存在
        if not fs.exists(ObjectId(file_id)):
            print(f"File not found in GridFS: {file_id}")
            return jsonify({'error': 'File not found'}), 404
            
        file = fs.get(ObjectId(file_id))
        print(f"File found: {file.filename}, type: {file.content_type}")
        
        # 读取文件内容
        file_data = file.read()
        if not file_data:
            print(f"File is empty: {file_id}")
            return jsonify({'error': 'File is empty'}), 404
            
        return send_file(
            io.BytesIO(file_data),
            mimetype=file.content_type,
            as_attachment=False
        )
    except Exception as e:
        print(f"Error getting file: {str(e)}")
        return jsonify({'error': str(e)}), 404

@media_bp.route('/<file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    try:
        fs.delete(ObjectId(file_id))
        return jsonify({'message': 'File deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 404 