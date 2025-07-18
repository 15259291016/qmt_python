"""
数据库配置文件
统一管理MySQL连接配置
"""

# 数据库连接配置
DB_CONFIG = {
    'host': '120.26.202.151',
    'port': 3306,
    'user': 'root',
    'password': '611698',
    'database': 'stock_data',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'pool_size': 5,
    'pool_name': 'stock_pool',
    'pool_reset_session': True,
    'connect_timeout': 60,
    'read_timeout': 30,
    'write_timeout': 30
}

# 数据库连接字符串（用于某些ORM框架）
DATABASE_URL = f"mysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"

# 连接池配置
POOL_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# 数据库表前缀（可选）
TABLE_PREFIX = ''

# 数据库备份配置
BACKUP_CONFIG = {
    'backup_dir': './backups',
    'backup_retention_days': 30,
    'backup_time': '02:00',  # 每天凌晨2点备份
    'compress_backup': True
}

# 数据库监控配置
MONITOR_CONFIG = {
    'enable_monitoring': True,
    'slow_query_threshold': 1.0,  # 秒
    'max_connections_warning': 80,
    'connection_timeout_warning': 5.0  # 秒
}

# 环境配置
ENVIRONMENT = {
    'development': {
        'host': '120.26.202.151',
        'port': 3306,
        'database': 'stock_data_dev'
    },
    'testing': {
        'host': '120.26.202.151',
        'port': 3306,
        'database': 'stock_data_test'
    },
    'production': {
        'host': '120.26.202.151',
        'port': 3306,
        'database': 'stock_data'
    }
}

def get_db_config(env='production'):
    """根据环境获取数据库配置"""
    config = DB_CONFIG.copy()
    if env in ENVIRONMENT:
        env_config = ENVIRONMENT[env]
        config.update(env_config)
    return config

def get_connection_string(env='production'):
    """获取数据库连接字符串"""
    config = get_db_config(env)
    return f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}" 