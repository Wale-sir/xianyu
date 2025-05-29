from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from models.food import Food
from bson.objectid import ObjectId
from extensions import mongo
from gridfs import GridFS
from models.relationship import Relationship
from models.search import Search
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, FileField
from wtforms.validators import DataRequired, Length, NumberRange
from datetime import datetime

food_bp = Blueprint('food', __name__, url_prefix='/food')
fs = GridFS(mongo.db)

class FoodForm(FlaskForm):
    name = StringField('名称', validators=[DataRequired(message='请输入名称'), Length(min=2, max=50, message='名称长度必须在2-50个字符之间')])
    description = TextAreaField('描述', validators=[DataRequired(message='请输入描述'), Length(min=10, max=500, message='描述长度必须在10-500个字符之间')])
    price = FloatField('价格', validators=[DataRequired(message='请输入价格'), NumberRange(min=0, message='价格必须大于等于0')])
    image = FileField('图片')

@food_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    cursor = Food.get_all().skip((page - 1) * per_page).limit(per_page)
    foods = [Food(food) for food in cursor]
    total = mongo.db.foods.count_documents({})
    
    # 获取热门搜索
    popular_searches = Search.get_popular_searches(limit=5)
    print("Popular searches:", popular_searches)  # 添加调试信息
    
    return render_template('food/index.html',
                         foods=foods,
                         page=page,
                         per_page=per_page,
                         total=total,
                         popular_searches=popular_searches)

@food_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = FoodForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                name = form.name.data
                description = form.description.data
                price = form.price.data
                image = request.files.get('image')
                
                # 如果有图片，直接上传到 GridFS
                image_id = None
                if image:
                    try:
                        # 保存原始文件名和内容类型
                        original_filename = image.filename
                        original_content_type = image.content_type
                        print(f"Uploading file: {original_filename}, type: {original_content_type}")
                        
                        # 如果是图片，进行压缩
                        if image.content_type.startswith('image/'):
                            from PIL import Image
                            import io
                            img = Image.open(image)
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
                            image = img_io
                            # 更新内容类型为 JPEG
                            original_content_type = 'image/jpeg'
                        
                        # 确保文件指针在开始位置
                        if hasattr(image, 'seek'):
                            image.seek(0)
                        
                        # 上传文件并获取文件ID
                        file_id = fs.put(
                            image,
                            filename=original_filename,
                            content_type=original_content_type
                        )
                        
                        # 验证文件是否真的存在
                        if not fs.exists(file_id):
                            raise Exception("File was not properly stored in GridFS")
                        
                        # 使用字符串形式的文件ID
                        image_id = str(file_id)
                        print(f"File uploaded successfully, ID: {image_id}")
                        
                    except Exception as e:
                        print(f"Error uploading file: {str(e)}")
                        flash(f'图片上传出错: {str(e)}')
                        return render_template('food/create.html', form=form)
                
                food = Food.create(
                    name=name,
                    user_id=current_user.id,
                    description=description,
                    price=price,
                    image=image_id
                )
                
                if food:
                    flash('美食发布成功！')
                    return redirect(url_for('food.detail', food_id=food.id))
                flash('发布失败，请重试')
            except Exception as e:
                print(f"Error creating food: {str(e)}")
                flash('创建美食时发生错误')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}')
    return render_template('food/create.html', form=form)

@food_bp.route('/<food_id>')
def detail(food_id):
    try:
        food = Food.get_by_id(food_id)
        if not food:
            flash('美食不存在')
            return redirect(url_for('food.index'))
            
        # 获取关注状态
        is_following = False
        if current_user.is_authenticated:
            is_following = Relationship.is_following(current_user.id, food.user_id)
            
        return render_template('food/detail.html', food=food, is_following=is_following)
    except Exception as e:
        print(f"Error getting food detail: {str(e)}")
        flash('获取美食详情失败')
        return redirect(url_for('food.index'))

@food_bp.route('/nearby')
def nearby():
    longitude = request.args.get('longitude', type=float)
    latitude = request.args.get('latitude', type=float)
    max_distance = request.args.get('max_distance', 10000, type=int)
    
    if not all([longitude, latitude]):
        return jsonify({'error': 'Missing coordinates'}), 400
    
    foods = Food.get_nearby(longitude, latitude, max_distance)
    return jsonify(foods)

@food_bp.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Missing search query'}), 400
    
    # 获取搜索结果
    foods = Food.search(query)
    
    # 如果是 AJAX 请求（用于搜索建议），只返回结果，不记录搜索历史
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([{
            '_id': str(food['_id']),
            'name': food['name'],
            'price': food['price'],
            'description': food['description']
        } for food in foods])
    
    # 只有在非 AJAX 请求（实际搜索）时才保存搜索记录
    if current_user.is_authenticated:
        Search.save_search(current_user.id, query)
    
    # 返回搜索结果页面
    return render_template('food/search_results.html',
                         foods=foods,
                         query=query)

@food_bp.route('/price-range')
def price_range():
    min_price = request.args.get('min', type=float)
    max_price = request.args.get('max', type=float)
    
    if not all([min_price, max_price]):
        return jsonify({'error': 'Missing price range'}), 400
    
    foods = Food.get_by_price_range(min_price, max_price)
    return jsonify(foods)

@food_bp.route('/rating')
def rating():
    min_rating = request.args.get('min', type=float)
    if min_rating is None:
        return jsonify({'error': 'Missing minimum rating'}), 400
    
    foods = Food.get_by_rating(min_rating)
    return jsonify(foods)

@food_bp.route('/tags/popular')
def popular_tags():
    limit = request.args.get('limit', 10, type=int)
    tags = Food.get_popular_tags(limit)
    return jsonify(tags)

@food_bp.route('/<food_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(food_id):
    print(f"尝试编辑美食，ID: {food_id}")
    try:
        food = Food.get_by_id(food_id)
        print(f"获取到的美食对象: {food}")
        
        if not food:
            flash('美食不存在', 'error')
            return redirect(url_for('food.index'))
            
        if str(food.user_id) != str(current_user.id):
            flash('您没有权限编辑这个美食', 'error')
            return redirect(url_for('food.detail', food_id=food_id))
            
        form = FoodForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                update_data = {
                    'name': form.name.data,
                    'description': form.description.data,
                    'price': float(form.price.data),
                    'updated_at': datetime.utcnow()
                }
                
                if form.image.data:
                    try:
                        file = File.save_file(form.image.data)
                        if file:
                            update_data['image'] = str(file.id)
                    except Exception as e:
                        print(f"图片上传失败: {str(e)}")
                        flash('图片上传失败', 'error')
                        return render_template('food/edit.html', food=food, form=form)
                
                try:
                    result = mongo.db.foods.update_one(
                        {'_id': ObjectId(food_id)},
                        {'$set': update_data}
                    )
                    if result.modified_count > 0:
                        flash('美食信息更新成功', 'success')
                        return redirect(url_for('food.detail', food_id=food_id))
                    else:
                        flash('没有更改任何信息', 'info')
                except Exception as e:
                    print(f"更新美食失败: {str(e)}")
                    flash('更新失败，请稍后重试', 'error')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"{getattr(form, field).label.text}: {error}", 'error')
        else:
            form.name.data = food.name
            form.description.data = food.description
            form.price.data = food.price
            
        return render_template('food/edit.html', food=food, form=form)
    except Exception as e:
        print(f"编辑路由发生错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        flash('发生错误，请稍后重试', 'error')
        return redirect(url_for('food.index'))

@food_bp.route('/<food_id>/delete', methods=['POST'])
@login_required
def delete(food_id):
    try:
        food = Food.get_by_id(food_id)
        if not food:
            flash('美食不存在', 'error')
            return redirect(url_for('food.index'))
        
        if str(food.user_id) != current_user.id:
            flash('您没有权限删除这个美食', 'error')
            return redirect(url_for('food.detail', food_id=food_id))
        
        # 删除美食
        food.delete()
        flash('美食删除成功', 'success')
        return redirect(url_for('food.index'))
    except Exception as e:
        print(f"删除美食失败: {str(e)}")
        flash('删除失败，请稍后重试', 'error')
        return redirect(url_for('food.index'))

@food_bp.route('/<food_id>/review', methods=['POST'])
@login_required
def add_review(food_id):
    try:
        rating = float(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        
        if not comment:
            flash('请输入评论内容', 'error')
            return redirect(url_for('food.detail', food_id=food_id))
            
        if rating < 1 or rating > 5:
            flash('评分必须在1-5之间', 'error')
            return redirect(url_for('food.detail', food_id=food_id))
            
        food = Food.get_by_id(food_id)
        if not food:
            flash('美食不存在', 'error')
            return redirect(url_for('food.index'))
            
        # 直接调用静态方法
        Food.add_review(food_id, current_user.id, rating, comment)
        flash('评论发布成功', 'success')
        return redirect(url_for('food.detail', food_id=food_id))
    except Exception as e:
        print(f"添加评论失败: {str(e)}")
        flash('评论发布失败，请稍后重试', 'error')
        return redirect(url_for('food.detail', food_id=food_id)) 