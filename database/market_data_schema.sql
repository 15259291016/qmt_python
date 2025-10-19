-- 市场数据存储数据库设计
-- 专门用于记录市场数据，为量化AI模型准备
-- 数据库名: market_data
-- 创建时间: 2025-01-15

-- 创建数据库
CREATE DATABASE IF NOT EXISTS market_data 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE market_data;

-- ========================================
-- 1. 股票基础信息表
-- ========================================

CREATE TABLE IF NOT EXISTS stock_basic (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    area VARCHAR(50) COMMENT '地域',
    industry VARCHAR(50) COMMENT '所属行业',
    market VARCHAR(20) COMMENT '市场类型',
    list_date DATE COMMENT '上市日期',
    delist_date DATE COMMENT '退市日期',
    is_hs VARCHAR(10) COMMENT '是否沪深港通标的',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ts_code (ts_code),
    UNIQUE KEY uk_symbol (symbol),
    INDEX idx_industry (industry),
    INDEX idx_market (market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基础信息表';

-- ========================================
-- 2. 迅投市场数据表
-- ========================================

-- 3秒级别tick数据表
CREATE TABLE IF NOT EXISTS tick_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    tick_time DATETIME(3) NOT NULL COMMENT 'tick时间（精确到毫秒）',
    last_price DECIMAL(10,4) NOT NULL COMMENT '最新价',
    volume BIGINT NOT NULL COMMENT '成交量',
    amount DECIMAL(20,4) NOT NULL COMMENT '成交金额',
    bid_price1 DECIMAL(10,4) COMMENT '买一价',
    bid_volume1 BIGINT COMMENT '买一量',
    ask_price1 DECIMAL(10,4) COMMENT '卖一价',
    ask_volume1 BIGINT COMMENT '卖一量',
    bid_price2 DECIMAL(10,4) COMMENT '买二价',
    bid_volume2 BIGINT COMMENT '买二量',
    ask_price2 DECIMAL(10,4) COMMENT '卖二价',
    ask_volume2 BIGINT COMMENT '卖二量',
    bid_price3 DECIMAL(10,4) COMMENT '买三价',
    bid_volume3 BIGINT COMMENT '买三量',
    ask_price3 DECIMAL(10,4) COMMENT '卖三价',
    ask_volume3 BIGINT COMMENT '卖三量',
    bid_price4 DECIMAL(10,4) COMMENT '买四价',
    bid_volume4 BIGINT COMMENT '买四量',
    ask_price4 DECIMAL(10,4) COMMENT '卖四价',
    ask_volume4 BIGINT COMMENT '卖四量',
    bid_price5 DECIMAL(10,4) COMMENT '买五价',
    bid_volume5 BIGINT COMMENT '买五量',
    ask_price5 DECIMAL(10,4) COMMENT '卖五价',
    ask_volume5 BIGINT COMMENT '卖五量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_time (symbol, tick_time),
    INDEX idx_symbol (symbol),
    INDEX idx_tick_time (tick_time),
    INDEX idx_symbol_time_desc (symbol, tick_time DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='3秒级别tick数据表';

-- 分钟级数据表
CREATE TABLE IF NOT EXISTS minute_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    datetime DATETIME NOT NULL COMMENT '时间',
    open DECIMAL(10,4) NOT NULL COMMENT '开盘价',
    high DECIMAL(10,4) NOT NULL COMMENT '最高价',
    low DECIMAL(10,4) NOT NULL COMMENT '最低价',
    close DECIMAL(10,4) NOT NULL COMMENT '收盘价',
    volume BIGINT NOT NULL COMMENT '成交量',
    amount DECIMAL(20,4) NOT NULL COMMENT '成交金额',
    period VARCHAR(10) DEFAULT '1min' COMMENT '周期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_datetime (symbol, datetime),
    INDEX idx_symbol (symbol),
    INDEX idx_datetime (datetime),
    INDEX idx_symbol_datetime_desc (symbol, datetime DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分钟级数据表';

-- 日线数据表
CREATE TABLE IF NOT EXISTS daily_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,4) NOT NULL COMMENT '开盘价',
    high DECIMAL(10,4) NOT NULL COMMENT '最高价',
    low DECIMAL(10,4) NOT NULL COMMENT '最低价',
    close DECIMAL(10,4) NOT NULL COMMENT '收盘价',
    pre_close DECIMAL(10,4) COMMENT '昨收价',
    change_amount DECIMAL(10,4) COMMENT '涨跌额',
    pct_chg DECIMAL(8,4) COMMENT '涨跌幅',
    volume BIGINT NOT NULL COMMENT '成交量',
    amount DECIMAL(20,4) NOT NULL COMMENT '成交金额',
    turnover_rate DECIMAL(8,4) COMMENT '换手率',
    pe_ttm DECIMAL(10,4) COMMENT '市盈率TTM',
    pb DECIMAL(10,4) COMMENT '市净率',
    ps_ttm DECIMAL(10,4) COMMENT '市销率TTM',
    dv_ratio DECIMAL(8,4) COMMENT '股息率',
    total_mv DECIMAL(20,4) COMMENT '总市值',
    circ_mv DECIMAL(20,4) COMMENT '流通市值',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_trade_date (trade_date),
    INDEX idx_symbol_date_desc (symbol, trade_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日线数据表';

-- 复权因子表
CREATE TABLE IF NOT EXISTS adj_factor (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    adj_factor DECIMAL(10,6) NOT NULL COMMENT '复权因子',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复权因子表';

-- ========================================
-- 3. 技术指标表
-- ========================================

CREATE TABLE IF NOT EXISTS technical_indicators (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    -- 移动平均线
    ma5 DECIMAL(10,4) COMMENT '5日均线',
    ma10 DECIMAL(10,4) COMMENT '10日均线',
    ma20 DECIMAL(10,4) COMMENT '20日均线',
    ma60 DECIMAL(10,4) COMMENT '60日均线',
    ma120 DECIMAL(10,4) COMMENT '120日均线',
    ma250 DECIMAL(10,4) COMMENT '250日均线',
    -- MACD指标
    macd_dif DECIMAL(10,4) COMMENT 'MACD DIF',
    macd_dea DECIMAL(10,4) COMMENT 'MACD DEA',
    macd_histogram DECIMAL(10,4) COMMENT 'MACD 柱状图',
    -- RSI指标
    rsi6 DECIMAL(8,4) COMMENT 'RSI6',
    rsi12 DECIMAL(8,4) COMMENT 'RSI12',
    rsi24 DECIMAL(8,4) COMMENT 'RSI24',
    -- KDJ指标
    kdj_k DECIMAL(8,4) COMMENT 'KDJ K值',
    kdj_d DECIMAL(8,4) COMMENT 'KDJ D值',
    kdj_j DECIMAL(8,4) COMMENT 'KDJ J值',
    -- 布林带
    boll_upper DECIMAL(10,4) COMMENT '布林带上轨',
    boll_middle DECIMAL(10,4) COMMENT '布林带中轨',
    boll_lower DECIMAL(10,4) COMMENT '布林带下轨',
    -- 其他指标
    atr DECIMAL(10,4) COMMENT 'ATR',
    cci DECIMAL(10,4) COMMENT 'CCI',
    williams_r DECIMAL(8,4) COMMENT '威廉指标',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技术指标表';

-- ========================================
-- 4. 数据同步状态表
-- ========================================

CREATE TABLE IF NOT EXISTS data_sync_status (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型',
    symbol VARCHAR(20) COMMENT '股票代码',
    last_sync_time DATETIME COMMENT '最后同步时间',
    sync_status VARCHAR(20) DEFAULT 'SUCCESS' COMMENT '同步状态',
    error_message TEXT COMMENT '错误信息',
    record_count INT DEFAULT 0 COMMENT '记录数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_data_type_symbol (data_type, symbol),
    INDEX idx_data_type (data_type),
    INDEX idx_sync_status (sync_status),
    INDEX idx_last_sync_time (last_sync_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据同步状态表';

-- ========================================
-- 5. 系统配置表
-- ========================================

CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(50) DEFAULT 'string' COMMENT '配置类型',
    description VARCHAR(200) COMMENT '描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_config_key (config_key),
    INDEX idx_config_type (config_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- ========================================
-- 6. 初始化数据
-- ========================================

-- 插入系统配置
INSERT INTO system_config (config_key, config_value, description, config_type) VALUES
('xtquant_server', 'localhost', '迅投服务器地址', 'string'),
('xtquant_port', '6001', '迅投服务器端口', 'number'),
('data_retention_days', '365', '数据保留天数', 'number'),
('tick_data_retention_days', '30', 'tick数据保留天数', 'number'),
('sync_batch_size', '1000', '同步批次大小', 'number'),
('max_workers', '10', '最大并发线程数', 'number');

-- ========================================
-- 7. 创建视图
-- ========================================

-- 股票综合信息视图
CREATE VIEW v_stock_summary AS
SELECT 
    sb.symbol,
    sb.name,
    sb.industry,
    sb.market,
    dd.close as latest_price,
    dd.pct_chg as latest_change,
    dd.trade_date as latest_date,
    dd.volume as latest_volume,
    dd.amount as latest_amount,
    dd.pe_ttm,
    dd.pb,
    dd.total_mv,
    dd.circ_mv
FROM stock_basic sb
LEFT JOIN daily_data dd ON sb.symbol = dd.symbol 
    AND dd.trade_date = (SELECT MAX(trade_date) FROM daily_data WHERE symbol = sb.symbol);

-- 数据统计视图
CREATE VIEW v_data_statistics AS
SELECT 
    'tick_data' as data_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT symbol) as unique_symbols,
    MIN(tick_time) as earliest_time,
    MAX(tick_time) as latest_time
FROM tick_data
UNION ALL
SELECT 
    'minute_data' as data_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT symbol) as unique_symbols,
    MIN(datetime) as earliest_time,
    MAX(datetime) as latest_time
FROM minute_data
UNION ALL
SELECT 
    'daily_data' as data_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT symbol) as unique_symbols,
    MIN(trade_date) as earliest_time,
    MAX(trade_date) as latest_time
FROM daily_data;

-- ========================================
-- 8. 创建存储过程
-- ========================================

DELIMITER //

-- 清理历史数据存储过程
CREATE PROCEDURE CleanHistoricalData(IN days_to_keep INT)
BEGIN
    DECLARE cutoff_date DATE;
    DECLARE tick_cutoff_date DATE;
    
    SET cutoff_date = DATE_SUB(CURDATE(), INTERVAL days_to_keep DAY);
    SET tick_cutoff_date = DATE_SUB(cutoff_date, INTERVAL 30 DAY);
    
    -- 清理tick数据（保留更短时间）
    DELETE FROM tick_data WHERE DATE(tick_time) < tick_cutoff_date;
    
    -- 清理分钟数据
    DELETE FROM minute_data WHERE DATE(datetime) < cutoff_date;
    
    -- 清理技术指标
    DELETE FROM technical_indicators WHERE trade_date < cutoff_date;
    
    -- 保留更长时间的日线数据
    DELETE FROM daily_data WHERE trade_date < DATE_SUB(cutoff_date, INTERVAL 365 DAY);
    
    -- 优化表
    OPTIMIZE TABLE tick_data;
    OPTIMIZE TABLE minute_data;
    OPTIMIZE TABLE daily_data;
    OPTIMIZE TABLE technical_indicators;
    
    SELECT ROW_COUNT() as deleted_rows;
END //

-- 计算技术指标存储过程
CREATE PROCEDURE CalculateTechnicalIndicators(IN p_symbol VARCHAR(20), IN p_days INT)
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
        WHERE symbol = p_symbol 
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
        WHERE symbol = p_symbol 
        AND trade_date <= v_date 
        ORDER BY trade_date DESC 
        LIMIT 5;
        
        SELECT AVG(close) INTO v_ma10 
        FROM daily_data 
        WHERE symbol = p_symbol 
        AND trade_date <= v_date 
        ORDER BY trade_date DESC 
        LIMIT 10;
        
        SELECT AVG(close) INTO v_ma20 
        FROM daily_data 
        WHERE symbol = p_symbol 
        AND trade_date <= v_date 
        ORDER BY trade_date DESC 
        LIMIT 20;
        
        -- 插入或更新技术指标
        INSERT INTO technical_indicators (symbol, trade_date, ma5, ma10, ma20)
        VALUES (p_symbol, v_date, v_ma5, v_ma10, v_ma20)
        ON DUPLICATE KEY UPDATE
        ma5 = VALUES(ma5),
        ma10 = VALUES(ma10),
        ma20 = VALUES(ma20);
        
    END LOOP;
    
    CLOSE cur;
END //

DELIMITER ;

-- ========================================
-- 9. 创建索引优化
-- ========================================

-- 为常用查询创建复合索引
CREATE INDEX idx_tick_data_symbol_time ON tick_data(symbol, tick_time);
CREATE INDEX idx_daily_data_symbol_date ON daily_data(symbol, trade_date);
CREATE INDEX idx_minute_data_symbol_datetime ON minute_data(symbol, datetime);

-- ========================================
-- 10. 权限设置
-- ========================================

-- 创建只读用户
CREATE USER IF NOT EXISTS 'market_data_readonly'@'%' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON market_data.* TO 'market_data_readonly'@'%';

-- 创建应用用户
CREATE USER IF NOT EXISTS 'market_data_app'@'%' IDENTIFIED BY 'app_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON market_data.* TO 'market_data_app'@'%';

-- 创建管理员用户
CREATE USER IF NOT EXISTS 'market_data_admin'@'%' IDENTIFIED BY 'admin_password';
GRANT ALL PRIVILEGES ON market_data.* TO 'market_data_admin'@'%';

FLUSH PRIVILEGES;

COMMIT;
