-- MySQL数据库表结构
-- 量化交易平台数据库设计
-- 数据库名: stock_data

USE stock_data;

-- ========================================
-- 1. 股票基础信息表
-- ========================================

-- 股票列表表
CREATE TABLE IF NOT EXISTS stock_basic (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    area VARCHAR(50) COMMENT '地域',
    industry VARCHAR(50) COMMENT '所属行业',
    cnspell VARCHAR(50) COMMENT '拼音缩写',
    market VARCHAR(20) COMMENT '市场类型',
    list_date DATE COMMENT '上市日期',
    act_name VARCHAR(100) COMMENT '实际控制人',
    act_ent_type VARCHAR(50) COMMENT '企业类型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code (ts_code),
    INDEX idx_symbol (symbol),
    INDEX idx_industry (industry),
    INDEX idx_market (market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基础信息表';

-- ========================================
-- 2. 股票行情数据表
-- ========================================

-- 日线行情数据表
CREATE TABLE IF NOT EXISTS daily_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,4) COMMENT '开盘价',
    high DECIMAL(10,4) COMMENT '最高价',
    low DECIMAL(10,4) COMMENT '最低价',
    close DECIMAL(10,4) COMMENT '收盘价',
    pre_close DECIMAL(10,4) COMMENT '昨收价',
    change_amount DECIMAL(10,4) COMMENT '涨跌额',
    pct_chg DECIMAL(8,4) COMMENT '涨跌幅',
    vol DECIMAL(20,4) COMMENT '成交量',
    amount DECIMAL(20,4) COMMENT '成交额',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日线行情数据表';

-- 复权因子表
CREATE TABLE IF NOT EXISTS adj_factor (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    adj_factor DECIMAL(10,6) COMMENT '复权因子',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复权因子表';

-- 分钟级行情数据表
CREATE TABLE IF NOT EXISTS minute_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    trade_datetime DATETIME NOT NULL COMMENT '交易时间',
    open DECIMAL(10,4) COMMENT '开盘价',
    high DECIMAL(10,4) COMMENT '最高价',
    low DECIMAL(10,4) COMMENT '最低价',
    close DECIMAL(10,4) COMMENT '收盘价',
    vol DECIMAL(20,4) COMMENT '成交量',
    amount DECIMAL(20,4) COMMENT '成交额',
    period VARCHAR(10) DEFAULT '1min' COMMENT '周期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code_datetime (ts_code, trade_datetime),
    INDEX idx_trade_datetime (trade_datetime),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分钟级行情数据表';

-- ========================================
-- 3. 财务数据表
-- ========================================

-- 财务指标表
CREATE TABLE IF NOT EXISTS fina_indicator (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    end_date DATE NOT NULL COMMENT '报告期',
    roe DECIMAL(10,4) COMMENT '净资产收益率',
    grossprofit_margin DECIMAL(10,4) COMMENT '毛利率',
    ocfps DECIMAL(10,4) COMMENT '每股经营现金流',
    debt_to_assets DECIMAL(10,4) COMMENT '资产负债率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code_end_date (ts_code, end_date),
    INDEX idx_end_date (end_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务指标表';

-- 每日指标表
CREATE TABLE IF NOT EXISTS daily_basic (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    pe DECIMAL(10,4) COMMENT '市盈率',
    pb DECIMAL(10,4) COMMENT '市净率',
    ps_ttm DECIMAL(10,4) COMMENT '市销率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日指标表';

-- ========================================
-- 4. 订单管理表
-- ========================================

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL COMMENT '订单ID',
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    side VARCHAR(10) NOT NULL COMMENT '买卖方向',
    price DECIMAL(10,4) NOT NULL COMMENT '价格',
    quantity INT NOT NULL COMMENT '数量',
    status VARCHAR(20) DEFAULT 'NEW' COMMENT '订单状态',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    filled_quantity INT DEFAULT 0 COMMENT '已成交数量',
    avg_fill_price DECIMAL(10,4) DEFAULT 0 COMMENT '平均成交价',
    account VARCHAR(50) COMMENT '账户',
    broker_order_id VARCHAR(50) COMMENT '券商订单号',
    user_id VARCHAR(50) COMMENT '用户ID',
    ext JSON COMMENT '扩展字段',
    UNIQUE KEY uk_order_id (order_id),
    INDEX idx_symbol (symbol),
    INDEX idx_status (status),
    INDEX idx_account (account),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- ========================================
-- 5. 风控管理表
-- ========================================

-- 风控配置表
CREATE TABLE IF NOT EXISTS risk_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(200) COMMENT '描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风控配置表';

-- 股票黑名单表
CREATE TABLE IF NOT EXISTS stock_blacklist (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    reason VARCHAR(200) COMMENT '加入黑名单原因',
    added_by VARCHAR(50) COMMENT '添加人',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    UNIQUE KEY uk_symbol (symbol),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票黑名单表';

-- 风控日志表
CREATE TABLE IF NOT EXISTS risk_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) COMMENT '用户ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    symbol VARCHAR(20) COMMENT '股票代码',
    price DECIMAL(10,4) COMMENT '价格',
    quantity INT COMMENT '数量',
    reason VARCHAR(200) COMMENT '原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_symbol (symbol),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风控日志表';

-- ========================================
-- 6. 合规管理表
-- ========================================

-- 合规规则表
CREATE TABLE IF NOT EXISTS compliance_rules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(50) NOT NULL COMMENT '规则类型',
    rule_config JSON COMMENT '规则配置',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rule_name (rule_name),
    INDEX idx_rule_type (rule_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合规规则表';

-- 合规日志表
CREATE TABLE IF NOT EXISTS compliance_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) COMMENT '用户ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    order_info JSON COMMENT '订单信息',
    rule_id BIGINT COMMENT '规则ID',
    result BOOLEAN COMMENT '检查结果',
    message VARCHAR(200) COMMENT '消息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_rule_id (rule_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合规日志表';

-- ========================================
-- 7. 审计日志表
-- ========================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) COMMENT '用户ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    resource_type VARCHAR(50) COMMENT '资源类型',
    resource_id VARCHAR(50) COMMENT '资源ID',
    details JSON COMMENT '详细信息',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource_type (resource_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';

-- ========================================
-- 8. 策略相关表
-- ========================================

-- 策略配置表
CREATE TABLE IF NOT EXISTS strategy_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL COMMENT '策略名称',
    strategy_type VARCHAR(50) NOT NULL COMMENT '策略类型',
    config JSON COMMENT '策略配置',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_strategy_name (strategy_name),
    INDEX idx_strategy_type (strategy_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='策略配置表';

-- 策略信号表
CREATE TABLE IF NOT EXISTS strategy_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL COMMENT '策略名称',
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    signal_type VARCHAR(20) NOT NULL COMMENT '信号类型',
    signal_value DECIMAL(10,4) COMMENT '信号值',
    trade_date DATE NOT NULL COMMENT '交易日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy_name (strategy_name),
    INDEX idx_symbol (symbol),
    INDEX idx_signal_type (signal_type),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='策略信号表';

-- ========================================
-- 9. 回测相关表
-- ========================================

-- 回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL COMMENT '策略名称',
    account_id VARCHAR(50) NOT NULL COMMENT '账户ID',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '结束日期',
    initial_capital DECIMAL(20,4) NOT NULL COMMENT '初始资金',
    final_capital DECIMAL(20,4) NOT NULL COMMENT '最终资金',
    total_return DECIMAL(10,4) COMMENT '总收益率',
    annual_return DECIMAL(10,4) COMMENT '年化收益率',
    sharpe_ratio DECIMAL(10,4) COMMENT '夏普比率',
    max_drawdown DECIMAL(10,4) COMMENT '最大回撤',
    win_rate DECIMAL(10,4) COMMENT '胜率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy_name (strategy_name),
    INDEX idx_account_id (account_id),
    INDEX idx_start_date (start_date),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回测结果表';

-- 回测交易记录表
CREATE TABLE IF NOT EXISTS backtest_trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    backtest_id BIGINT NOT NULL COMMENT '回测ID',
    trade_datetime DATETIME NOT NULL COMMENT '交易时间',
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    side VARCHAR(10) NOT NULL COMMENT '买卖方向',
    price DECIMAL(10,4) NOT NULL COMMENT '价格',
    quantity INT NOT NULL COMMENT '数量',
    commission DECIMAL(10,4) COMMENT '手续费',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_backtest_id (backtest_id),
    INDEX idx_symbol (symbol),
    INDEX idx_trade_datetime (trade_datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回测交易记录表';

-- ========================================
-- 10. 统计分析表
-- ========================================

-- 统计结果表
CREATE TABLE IF NOT EXISTS statistics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE NOT NULL COMMENT '交易日期',
    annual_return DECIMAL(10,4) COMMENT '年化收益率',
    max_drawdown DECIMAL(10,4) COMMENT '最大回撤',
    sharpe_ratio DECIMAL(10,4) COMMENT '夏普比率',
    strategy_annual_return DECIMAL(10,4) COMMENT '策略年化收益率',
    strategy_max_drawdown DECIMAL(10,4) COMMENT '策略最大回撤',
    strategy_sharpe_ratio DECIMAL(10,4) COMMENT '策略夏普比率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_trade_date (trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='统计结果表';

-- 机器学习结果表
CREATE TABLE IF NOT EXISTS ml_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE NOT NULL COMMENT '交易日期',
    mse_lr DECIMAL(10,6) COMMENT '线性回归MSE',
    mse_rf DECIMAL(10,6) COMMENT '随机森林MSE',
    mse_xgb DECIMAL(10,6) COMMENT 'XGBoost MSE',
    mse_lstm DECIMAL(10,6) COMMENT 'LSTM MSE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_trade_date (trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器学习结果表';

-- ========================================
-- 11. 系统配置表
-- ========================================

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(200) COMMENT '描述',
    config_type VARCHAR(50) DEFAULT 'string' COMMENT '配置类型',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_config_key (config_key),
    INDEX idx_config_type (config_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- ========================================
-- 12. 初始化数据
-- ========================================

-- 插入系统配置
INSERT INTO system_config (config_key, config_value, description, config_type) VALUES
('max_single_order_amount', '1000000', '单笔最大下单金额', 'number'),
('max_daily_amount', '10000000', '日内最大下单金额', 'number'),
('risk_free_rate', '0.02', '无风险利率', 'number'),
('default_commission', '0.0003', '默认手续费率', 'number'),
('default_slippage', '0.0005', '默认滑点', 'number');

-- 插入风控配置
INSERT INTO risk_config (config_key, config_value, description) VALUES
('max_single_order_amount', '1000000', '单笔最大下单金额'),
('max_daily_amount', '10000000', '日内最大下单金额'),
('max_position_per_stock', '0.1', '单只股票最大仓位'),
('max_industry_weight', '0.3', '单一行业最大权重');

-- 插入合规规则
INSERT INTO compliance_rules (rule_name, rule_type, rule_config) VALUES
('交易时间检查', 'time_check', '{"start_time": "09:30", "end_time": "15:00"}'),
('涨跌停检查', 'price_limit', '{"max_up_limit": 0.1, "max_down_limit": 0.1}'),
('交易量检查', 'volume_check', '{"min_volume": 100, "max_volume": 1000000}');

-- 插入策略配置
INSERT INTO strategy_config (strategy_name, strategy_type, config) VALUES
('SimpleMA', 'ma_cross', '{"short_window": 5, "long_window": 20}'),
('RSI', 'rsi', '{"rsi_window": 14, "oversold": 30, "overbought": 70}'),
('MACD', 'macd', '{"fast_period": 12, "slow_period": 26, "signal_period": 9}');

-- ========================================
-- 13. 创建视图
-- ========================================

-- 股票综合信息视图
CREATE VIEW v_stock_summary AS
SELECT 
    sb.ts_code,
    sb.symbol,
    sb.name,
    sb.industry,
    dd.close as latest_price,
    dd.pct_chg as latest_change,
    dd.trade_date as latest_date,
    db.pe,
    db.pb,
    fi.roe,
    fi.grossprofit_margin
FROM stock_basic sb
LEFT JOIN daily_data dd ON sb.ts_code = dd.ts_code 
    AND dd.trade_date = (SELECT MAX(trade_date) FROM daily_data WHERE ts_code = sb.ts_code)
LEFT JOIN daily_basic db ON sb.ts_code = db.ts_code 
    AND db.trade_date = (SELECT MAX(trade_date) FROM daily_basic WHERE ts_code = sb.ts_code)
LEFT JOIN fina_indicator fi ON sb.ts_code = fi.ts_code 
    AND fi.end_date = (SELECT MAX(end_date) FROM fina_indicator WHERE ts_code = sb.ts_code);

-- 订单统计视图
CREATE VIEW v_order_summary AS
SELECT 
    DATE(create_time) as order_date,
    side,
    status,
    COUNT(*) as order_count,
    SUM(quantity * price) as total_amount,
    AVG(price) as avg_price
FROM orders
GROUP BY DATE(create_time), side, status;

-- ========================================
-- 14. 创建存储过程
-- ========================================

DELIMITER //

-- 清理历史数据存储过程
CREATE PROCEDURE CleanHistoricalData(IN days_to_keep INT)
BEGIN
    DECLARE cutoff_date DATE;
    SET cutoff_date = DATE_SUB(CURDATE(), INTERVAL days_to_keep DAY);
    
    DELETE FROM daily_data WHERE trade_date < cutoff_date;
    DELETE FROM minute_data WHERE trade_datetime < cutoff_date;
    DELETE FROM daily_basic WHERE trade_date < cutoff_date;
    DELETE FROM strategy_signals WHERE trade_date < cutoff_date;
    
    SELECT ROW_COUNT() as deleted_rows;
END //

-- 计算股票技术指标存储过程
CREATE PROCEDURE CalculateTechnicalIndicators(IN p_ts_code VARCHAR(20), IN p_days INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_date DATE;
    DECLARE v_close DECIMAL(10,4);
    DECLARE v_ma5 DECIMAL(10,4);
    DECLARE v_ma10 DECIMAL(10,4);
    DECLARE v_ma20 DECIMAL(10,4);
    
    DECLARE cur CURSOR FOR 
        SELECT trade_date, close 
        FROM daily_data 
        WHERE ts_code = p_ts_code 
        ORDER BY trade_date DESC 
        LIMIT p_days;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO v_date, v_close;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- 计算移动平均线
        SELECT AVG(close) INTO v_ma5 
        FROM daily_data 
        WHERE ts_code = p_ts_code 
        AND trade_date <= v_date 
        ORDER BY trade_date DESC 
        LIMIT 5;
        
        SELECT AVG(close) INTO v_ma10 
        FROM daily_data 
        WHERE ts_code = p_ts_code 
        AND trade_date <= v_date 
        ORDER BY trade_date DESC 
        LIMIT 10;
        
        SELECT AVG(close) INTO v_ma20 
        FROM daily_data 
        WHERE ts_code = p_ts_code 
        AND trade_date <= v_date 
        ORDER BY trade_date DESC 
        LIMIT 20;
        
        -- 这里可以插入到技术指标表中
        -- INSERT INTO technical_indicators (ts_code, trade_date, ma5, ma10, ma20) 
        -- VALUES (p_ts_code, v_date, v_ma5, v_ma10, v_ma20);
        
    END LOOP;
    
    CLOSE cur;
END //

DELIMITER ;

-- ========================================
-- 15. 创建触发器
-- ========================================

-- 订单状态更新触发器
DELIMITER //
CREATE TRIGGER tr_orders_update
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
        VALUES (NEW.user_id, 'order_status_change', 'order', NEW.order_id, 
                JSON_OBJECT('old_status', OLD.status, 'new_status', NEW.status));
    END IF;
END //
DELIMITER ;

-- 风控日志触发器
DELIMITER //
CREATE TRIGGER tr_risk_logs_insert
AFTER INSERT ON risk_logs
FOR EACH ROW
BEGIN
    -- 如果风控检查失败，可以在这里添加额外的处理逻辑
    IF NEW.action = 'order_rejected' THEN
        -- 可以发送通知或记录到其他表
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
        VALUES (NEW.user_id, 'risk_check_failed', 'order', NULL, 
                JSON_OBJECT('symbol', NEW.symbol, 'reason', NEW.reason));
    END IF;
END //
DELIMITER ;

-- ========================================
-- 16. 创建索引优化
-- ========================================

-- 为常用查询创建复合索引
CREATE INDEX idx_daily_data_ts_date ON daily_data(ts_code, trade_date);
CREATE INDEX idx_orders_user_time ON orders(user_id, create_time);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at);
CREATE INDEX idx_strategy_signals_date_symbol ON strategy_signals(trade_date, symbol);

-- ========================================
-- 17. 权限设置
-- ========================================

-- 创建只读用户
CREATE USER IF NOT EXISTS 'stock_readonly'@'%' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON stock_data.* TO 'stock_readonly'@'%';

-- 创建应用用户
CREATE USER IF NOT EXISTS 'stock_app'@'%' IDENTIFIED BY 'app_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON stock_data.* TO 'stock_app'@'%';

-- 创建管理员用户
CREATE USER IF NOT EXISTS 'stock_admin'@'%' IDENTIFIED BY 'admin_password';
GRANT ALL PRIVILEGES ON stock_data.* TO 'stock_admin'@'%';

FLUSH PRIVILEGES;

-- ========================================
-- 18. 数据库优化设置
-- ========================================

-- 设置InnoDB缓冲池大小（根据服务器内存调整）
-- SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB

-- 设置查询缓存
-- SET GLOBAL query_cache_size = 67108864; -- 64MB
-- SET GLOBAL query_cache_type = 1;

-- 设置连接数
-- SET GLOBAL max_connections = 200;

-- 设置慢查询日志
-- SET GLOBAL slow_query_log = 1;
-- SET GLOBAL long_query_time = 2;

COMMIT; 