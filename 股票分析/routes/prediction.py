from flask import Blueprint, render_template, jsonify, request
from models.stock import Stock
from models.prediction import StockPrediction
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
from datetime import datetime, timedelta

prediction_bp = Blueprint('prediction', __name__)

def prepare_features(history_data):
    """准备特征数据"""
    df = pd.DataFrame(history_data)
    
    # 计算技术指标
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    
    # 计算RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 删除NaN值
    df = df.dropna()
    
    return df

def create_labels(df):
    """创建标签（1表示上涨，0表示下跌）"""
    df['label'] = (df['close'].shift(-1) > df['close']).astype(int)
    return df

@prediction_bp.route('/prediction/<stock_id>')
def predict_stock(stock_id):
    stock = Stock.get_by_id(stock_id)
    if not stock:
        return jsonify({'error': '股票不存在'}), 404
    
    # 获取历史数据
    history = Stock.get_stock_history(stock_id)
    if not history:
        return jsonify({'error': '没有足够的历史数据'}), 400
    
    # 准备数据
    df = prepare_features(history)
    df = create_labels(df)
    
    # 准备特征和标签
    features = ['MA5', 'MA10', 'MA20', 'RSI', 'MACD', 'Signal']
    X = df[features].values
    y = df['label'].values
    
    # 使用更简单的预测方法
    last_price = df['close'].iloc[-1]
    last_ma5 = df['MA5'].iloc[-1]
    last_ma10 = df['MA10'].iloc[-1]
    last_ma20 = df['MA20'].iloc[-1]
    last_rsi = df['RSI'].iloc[-1]
    last_macd = df['MACD'].iloc[-1]
    last_signal = df['Signal'].iloc[-1]
    
    # 基于技术指标的综合判断
    signals = []
    if last_price > last_ma5: signals.append(1)
    if last_price > last_ma10: signals.append(1)
    if last_price > last_ma20: signals.append(1)
    if last_rsi > 50: signals.append(1)
    if last_macd > last_signal: signals.append(1)
    
    # 计算上涨概率，处理空列表的情况
    if not signals:  # 如果没有信号，默认设置为中性
        up_probability = 0.5
    else:
        up_probability = sum(signals) / len(signals)
    
    prediction = 1 if up_probability > 0.5 else 0
    
    # 计算预测价格
    price_change = 0.01 if prediction == 1 else -0.01
    predicted_price = stock.current_price * (1 + price_change)
    
    # 保存预测结果
    prediction_data = {
        'stock_id': stock_id,
        'date': datetime.utcnow(),
        'predicted_price': float(predicted_price),
        'confidence': float(up_probability if prediction == 1 else 1 - up_probability),
        'direction': 'up' if prediction == 1 else 'down'
    }
    
    StockPrediction.create(prediction_data)
    
    return render_template('prediction/result.html',
                         stock=stock,
                         prediction=prediction_data)

@prediction_bp.route('/api/prediction/<stock_id>')
def get_prediction(stock_id):
    stock = Stock.get_by_id(stock_id)
    if not stock:
        return jsonify({'error': '股票不存在'}), 404
    
    predictions = StockPrediction.get_latest_predictions(stock_id)
    
    return jsonify({
        'predictions': [
            {
                'date': p.date,
                'predicted_price': p.predicted_price,
                'confidence': p.confidence,
                'direction': p.direction
            }
            for p in predictions
        ]
    }) 