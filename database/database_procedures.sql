-- 量化交易平台存储过程和触发器
-- 使用正确的DELIMITER语法

-- 清理历史数据的存储过程
DELIMITER //

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

-- 计算技术指标的存储过程
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
        ORDER BY trade_date;
    
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
        
        -- 更新或插入技术指标
        INSERT INTO daily_basic (ts_code, trade_date, ma5, ma10, ma20) 
        VALUES (p_ts_code, v_date, v_ma5, v_ma10, v_ma20)
        ON DUPLICATE KEY UPDATE 
            ma5 = v_ma5,
            ma10 = v_ma10,
            ma20 = v_ma20;
    END LOOP;
    
    CLOSE cur;
END //

DELIMITER ;

-- 订单更新触发器
DELIMITER //

CREATE TRIGGER tr_orders_update 
AFTER UPDATE ON orders 
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (
            NEW.user_id,
            'UPDATE_ORDER_STATUS',
            'orders',
            NEW.id,
            OLD.status,
            NEW.status,
            'SYSTEM'
        );
    END IF;
END //

-- 风控日志插入触发器
CREATE TRIGGER tr_risk_logs_insert 
AFTER INSERT ON risk_logs 
FOR EACH ROW
BEGIN
    IF NEW.risk_level = 'HIGH' THEN
        -- 发送高风险警报
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (
            NEW.user_id,
            'HIGH_RISK_ALERT',
            'risk_logs',
            NEW.id,
            NULL,
            NEW.risk_level,
            'SYSTEM'
        );
    END IF;
END //

DELIMITER ; 