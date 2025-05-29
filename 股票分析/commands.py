import click
from utils.data_generator import seed_database
from extensions import mongo
from app import create_app

app = create_app()

@click.group()
def cli():
    """股票分析系统命令行工具"""
    pass

@cli.command()
def seed():
    """生成模拟数据"""
    with app.app_context():
        click.echo('开始生成模拟数据...')
        seed_database()
        click.echo('模拟数据生成完成！')

@cli.command()
def clear():
    """清除所有数据"""
    with app.app_context():
        if click.confirm('确定要清除所有数据吗？此操作不可恢复！'):
            mongo.db.stocks.delete_many({})
            mongo.db.stock_history.delete_many({})
            mongo.db.stock_predictions.delete_many({})
            click.echo('所有数据已清除！')

if __name__ == '__main__':
    cli() 