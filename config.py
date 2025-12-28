# config.py

import os

# --- 1. 配置常量与基础路径 ---
# 获取项目根目录的绝对路径，用于构建数据库路径（如果使用 SQLite）
basedir = os.path.abspath(os.path.dirname(__file__))

# 上传文件存储路径
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
MATERIALS_FOLDER = os.path.join(UPLOAD_FOLDER, 'materials')
ASSIGNMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'assignments') 

# --- 2. SQL Server 连接参数 ---
# 🚨 警告：如果您连接失败，请尝试将此驱动名替换为以下之一：
#    - 'SQL Server Native Client 11.0'
#    - 'ODBC Driver 18 for SQL Server'
DB_DRIVER = 'ODBC Driver 17 for SQL Server' 
DB_SERVER = 'wuhl\\SQLEXPRESS'
DB_NAME = 'online_teaching_support_system' # 您的数据库名称

# --- 3. 配置基类 (Config) ---
class Config(object):
    """
    基础配置类，包含所有环境通用的配置项
    """
    # 文件上传配置
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MATERIALS_FOLDER = MATERIALS_FOLDER
    ASSIGNMENTS_FOLDER = ASSIGNMENTS_FOLDER
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 最大上传文件大小: 100MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'zip', 'rar', 'jpg', 'png', 'gif', 'xlsx', 'xls', 'mp4', 'avi'}
    
    # 🚨 核心密钥：必须替换为您生成的复杂随机字符串！！！
    # 示例：os.environ.get('SECRET_KEY') or '38914c44f3b79a55a6d5c64c1256e2f170e7a2b9e6f3b0c51f0c2a7e089297d0'
    SECRET_KEY = os.environ.get('SECRET_KEY') or '38914c44f3b79a55a6d5c64c1256e2f170e7a2b9e6f3b0c51f0c2a7e089297d0' 

    # -------------------------------------------------------------
    # 数据库配置 (SQLALCHEMY_DATABASE_URI)
    # 使用 mssql+pyodbc 驱动，通过 Windows 身份验证 (Trusted_Connection=yes)
    # -------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = (
        f'mssql+pyodbc:///?odbc_connect='
        f'DRIVER={DB_DRIVER};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_NAME};'
        f'Trusted_Connection=yes;'
    )
    
    # 禁用 SQLAlchemy 事件系统（通常推荐设为 False 以节省开销）
    SQLALCHEMY_TRACK_MODIFICATIONS = False 


# --- 4. 开发环境配置 (DevelopmentConfig) ---
class DevelopmentConfig(Config):
    """
    开发环境配置类，继承基础配置并开启调试模式
    """
    DEBUG = True # 开启调试模式，应用修改后自动重启，并显示详细错误信息


# --- 5. 生产环境配置示例 (ProductionConfig) ---
# 建议在实际部署时使用，强制关闭 DEBUG
class ProductionConfig(Config):
    """
    生产环境配置类，用于部署到生产服务器
    """
    DEBUG = False
    TESTING = False
    
    # ⚠️ 生产环境应严格通过环境变量设置数据库信息，确保安全
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')