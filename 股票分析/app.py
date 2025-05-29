from flask import Flask, render_template, send_from_directory, redirect, url_for
from dotenv import load_dotenv
import os
import signal
import sys
import logging
from extensions import init_extensions, login_manager, mongo
from models.indexes import create_indexes
from flask_wtf.csrf import CSRFProtect

# 加载环境变量
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/22102040235zzk')

    # 初始化 CSRF 保护
    csrf = CSRFProtect(app)

    # 初始化扩展
    init_extensions(app)

    # 创建索引
    create_indexes()

    # 配置用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.get_by_id(user_id)

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.stock import stock_bp
    from routes.visualization import visualization_bp
    from routes.prediction import prediction_bp
    from routes.share import share_bp

    # 注册所有蓝图
    app.register_blueprint(stock_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(visualization_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(share_bp)

    # 根路径路由
    @app.route('/')
    def index():
        return redirect(url_for('stock.index'))

    # 静态文件路由
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error=error), 500

    return app

def signal_handler(sig, frame):
    """处理关闭信号"""
    print("\n正在关闭服务器...")
    # 确保所有数据都已写入数据库
    mongo.db.client.close()
    print("数据库连接已关闭")
    sys.exit(0)

if __name__ == '__main__':
    app = create_app()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    print("服务器正在启动...")
    app.run(debug=True) 