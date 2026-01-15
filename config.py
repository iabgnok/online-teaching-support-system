"""应用配置文件"""

import os

# ==================== 基础路径配置 ====================
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
MATERIALS_FOLDER = os.path.join(UPLOAD_FOLDER, 'materials')
ASSIGNMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'assignments')

# ==================== 数据库连接参数 ====================
# 提示：如果连接失败，可尝试以下驱动：
# - 'SQL Server Native Client 11.0'
# - 'ODBC Driver 18 for SQL Server'
DB_DRIVER = 'ODBC Driver 17 for SQL Server'
DB_SERVER = 'wuhl\\SQLEXPRESS'
DB_NAME = 'online_teaching_support_system_db'

# ==================== 配置基类 ====================

class Config:
    """基础配置类"""
    
    # 文件上传配置
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MATERIALS_FOLDER = MATERIALS_FOLDER
    ASSIGNMENTS_FOLDER = ASSIGNMENTS_FOLDER
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'zip', 'rar',
        'jpg', 'png', 'gif', 'xlsx', 'xls', 'mp4', 'avi'
    }
    
    # 会话密钥（生产环境应使用环境变量）
    SECRET_KEY = os.environ.get('SECRET_KEY') or '38914c44f3b79a55a6d5c64c1256e2f170e7a2b9e6f3b0c51f0c2a7e089297d0'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = (
        f'mssql+pyodbc:///?odbc_connect='
        f'DRIVER={DB_DRIVER};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_NAME};'
        f'Trusted_Connection=yes;'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    # 生产环境应通过环境变量设置数据库连接
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')