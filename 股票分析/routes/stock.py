from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.stock import Stock
from datetime import datetime

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/stocks')
def index():
    stocks = Stock.get_all_stocks()
    return render_template('stock/index.html', stocks=stocks)

@stock_bp.route('/stocks/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        stock_data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'current_price': float(request.form.get('current_price')),
            'change_percent': float(request.form.get('change_percent')),
            'volume': int(request.form.get('volume')),
            'market_cap': float(request.form.get('market_cap')),
            'created_by': current_user.id,
            'created_at': datetime.utcnow()
        }
        
        stock = Stock.create(stock_data)
        flash('股票信息创建成功！', 'success')
        return redirect(url_for('stock.index'))
    
    return render_template('stock/create.html')

@stock_bp.route('/stocks/<stock_id>')
def view(stock_id):
    stock = Stock.get_by_id(stock_id)
    if not stock:
        flash('股票不存在！', 'error')
        return redirect(url_for('stock.index'))
    return render_template('stock/view.html', stock=stock)

@stock_bp.route('/stocks/<stock_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(stock_id):
    stock = Stock.get_by_id(stock_id)
    if not stock:
        flash('股票不存在！', 'error')
        return redirect(url_for('stock.index'))
    
    if request.method == 'POST':
        stock_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'current_price': float(request.form.get('current_price')),
            'change_percent': float(request.form.get('change_percent')),
            'volume': int(request.form.get('volume')),
            'market_cap': float(request.form.get('market_cap')),
            'updated_at': datetime.utcnow()
        }
        
        stock.update(stock_data)
        flash('股票信息更新成功！', 'success')
        return redirect(url_for('stock.view', stock_id=stock_id))
    
    return render_template('stock/edit.html', stock=stock)

@stock_bp.route('/stocks/<stock_id>/delete', methods=['POST'])
@login_required
def delete(stock_id):
    stock = Stock.get_by_id(stock_id)
    if not stock:
        flash('股票不存在！', 'error')
        return redirect(url_for('stock.index'))
    
    stock.delete()
    flash('股票信息删除成功！', 'success')
    return redirect(url_for('stock.index')) 