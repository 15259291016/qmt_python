# modules/data_service/api/tornado_integration.py
"""
Tornado集成模块
为现有的Tornado Web服务添加数据查询接口
"""
import json
import pandas as pd
from tornado.web import RequestHandler
from modules.data_service.integration import get_data_service_manager

class DataQueryHandler(RequestHandler):
    """数据查询处理器"""
    
    def get(self):
        """GET请求：查询股票数据"""
        try:
            ts_code = self.get_argument('ts_code', None)
            start_date = self.get_argument('start_date', None)
            end_date = self.get_argument('end_date', None)
            
            if not all([ts_code, start_date, end_date]):
                self.set_status(400)
                self.write({'error': '缺少必要参数: ts_code, start_date, end_date'})
                return
            
            data_manager = get_data_service_manager()
            df = data_manager.get_stock_data(ts_code, start_date, end_date)
            
            if df.empty:
                self.write({'data': [], 'message': '未找到数据'})
            else:
                self.write({
                    'data': df.to_dict(orient='records'),
                    'message': '查询成功',
                    'count': len(df)
                })
                
        except Exception as e:
            self.set_status(500)
            self.write({'error': f'查询失败: {str(e)}'})

class DataStatusHandler(RequestHandler):
    """数据状态查询处理器"""
    
    def get(self):
        """GET请求：查询数据完整性状态"""
        try:
            start_date = self.get_argument('start_date', None)
            end_date = self.get_argument('end_date', None)
            
            if not all([start_date, end_date]):
                self.set_status(400)
                self.write({'error': '缺少必要参数: start_date, end_date'})
                return
            
            data_manager = get_data_service_manager()
            status = data_manager.check_data_completeness(start_date, end_date)
            
            self.write({
                'status': status,
                'message': '查询成功'
            })
                
        except Exception as e:
            self.set_status(500)
            self.write({'error': f'查询失败: {str(e)}'})

class ManualCollectHandler(RequestHandler):
    """手动采集处理器"""
    
    def post(self):
        """POST请求：手动触发数据采集"""
        try:
            data = json.loads(self.request.body)
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            stock_list = data.get('stock_list', None)
            
            if not all([start_date, end_date]):
                self.set_status(400)
                self.write({'error': '缺少必要参数: start_date, end_date'})
                return
            
            data_manager = get_data_service_manager()
            
            # 在后台线程中执行采集，避免阻塞
            import threading
            def collect_worker():
                data_manager.manual_collect(start_date, end_date, stock_list)
            
            thread = threading.Thread(target=collect_worker, daemon=True)
            thread.start()
            
            self.write({
                'message': '采集任务已启动',
                'start_date': start_date,
                'end_date': end_date,
                'stock_list': stock_list
            })
                
        except Exception as e:
            self.set_status(500)
            self.write({'error': f'启动采集失败: {str(e)}'})

def add_data_handlers(app):
    """为Tornado应用添加数据查询路由"""
    app.add_handlers(r".*", [
        (r"/api/data/query", DataQueryHandler),
        (r"/api/data/status", DataStatusHandler),
        (r"/api/data/collect", ManualCollectHandler),
    ]) 