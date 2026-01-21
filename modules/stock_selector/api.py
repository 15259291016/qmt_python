import tornado.web
import json
from modules.stock_selector.selector import StockSelector

class StockSelectHandler(tornado.web.RequestHandler):
    def initialize(self, selector: StockSelector):
        self.selector = selector

    def get(self):
        wencai_query = self.get_argument('wencai', None)
        if wencai_query:
            result = self.selector.select_by_wencai(wencai_query)
            self.write({"selected_stocks": result})
            return
        min_pe = self.get_argument('min_pe', None)
        max_pe = self.get_argument('max_pe', None)
        min_mv = self.get_argument('min_mv', None)
        max_mv = self.get_argument('max_mv', None)
        industry = self.get_argument('industry', None)
        min_change = self.get_argument('min_change', None)
        max_change = self.get_argument('max_change', None)
        limit = int(self.get_argument('limit', '20'))
        ma_short = self.get_argument('ma_short', None)
        ma_long = self.get_argument('ma_long', None)
        ma_cross = None
        if ma_short and ma_long:
            ma_cross = {'short': int(ma_short), 'long': int(ma_long)}
        def to_float(x):
            try:
                return float(x) if x is not None else None
            except:
                return None
        result = self.selector.select(
            min_pe=to_float(min_pe),
            max_pe=to_float(max_pe),
            min_mv=to_float(min_mv),
            max_mv=to_float(max_mv),
            industry=industry,
            min_change=to_float(min_change),
            max_change=to_float(max_change),
            ma_cross=ma_cross,
            limit=limit
        )
        self.write({"selected_stocks": result})

    def post(self):
        try:
            params = json.loads(self.request.body)
        except Exception:
            params = {}
        wencai_query = params.get('wencai')
        if wencai_query:
            result = self.selector.select_by_wencai(wencai_query)
            self.write({"selected_stocks": result})
            return
        min_pe = params.get('min_pe')
        max_pe = params.get('max_pe')
        min_mv = params.get('min_mv')
        max_mv = params.get('max_mv')
        industry = params.get('industry')
        min_change = params.get('min_change')
        max_change = params.get('max_change')
        limit = params.get('limit', 20)
        ma_cross = params.get('ma_cross')
        result = self.selector.select(
            min_pe=min_pe,
            max_pe=max_pe,
            min_mv=min_mv,
            max_mv=max_mv,
            industry=industry,
            min_change=min_change,
            max_change=max_change,
            ma_cross=ma_cross,
            limit=limit
        )
        self.write({"selected_stocks": result})

class SectorRiskHandler(tornado.web.RequestHandler):
    """板块风险分析处理器"""
    def initialize(self, selector: StockSelector):
        self.selector = selector
    
    def get(self):
        """获取板块风险分析"""
        try:
            # 参数获取和验证
            try:
                period_days = int(self.get_argument('period_days', '30'))
            except ValueError:
                period_days = 30
            
            try:
                min_stocks = int(self.get_argument('min_stocks_per_sector', '5'))
            except ValueError:
                min_stocks = 5
            
            # 参数范围验证
            if period_days < 1 or period_days > 365:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": f"参数错误: period_days必须在1-365之间，当前值: {period_days}",
                    "data": {}
                })
                return
            
            if min_stocks < 1:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": f"参数错误: min_stocks_per_sector必须大于0，当前值: {min_stocks}",
                    "data": {}
                })
                return
            
            result = self.selector.analyze_sector_risk(
                period_days=period_days,
                min_stocks_per_sector=min_stocks
            )
            
            self.write({
                "code": 200,
                "msg": "success",
                "data": {
                    "sector_risks": result,
                    "total_sectors": len(result)
                }
            })
        except ValueError as e:
            self.set_status(400)
            self.write({
                "code": 400,
                "msg": f"参数错误: {str(e)}",
                "data": {}
            })
        except Exception as e:
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": f"板块风险分析失败: {str(e)}",
                "data": {}
            })


class HistoricalLowHandler(tornado.web.RequestHandler):
    """历史低位股票查询处理器"""
    def initialize(self, selector: StockSelector):
        self.selector = selector
    
    def get(self):
        """获取历史低位股票列表"""
        try:
            # 参数获取和验证
            try:
                period_days = int(self.get_argument('period_days', '250'))
            except ValueError:
                period_days = 250
            
            try:
                percentile = float(self.get_argument('percentile', '0.1'))
            except ValueError:
                percentile = 0.1
            
            try:
                min_price = float(self.get_argument('min_price', '1.0'))
            except ValueError:
                min_price = 1.0
            
            try:
                limit = int(self.get_argument('limit', '50'))
            except ValueError:
                limit = 50
            
            # 参数范围验证
            if period_days < 60 or period_days > 1000:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": f"参数错误: period_days必须在60-1000之间，当前值: {period_days}",
                    "data": {}
                })
                return
            
            if not 0.0 <= percentile <= 1.0:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": f"参数错误: percentile必须在0.0-1.0之间，当前值: {percentile}",
                    "data": {}
                })
                return
            
            if min_price < 0:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": f"参数错误: min_price必须大于等于0，当前值: {min_price}",
                    "data": {}
                })
                return
            
            if limit < 1 or limit > 200:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": f"参数错误: limit必须在1-200之间，当前值: {limit}",
                    "data": {}
                })
                return
            
            result = self.selector.find_historical_low_stocks(
                period_days=period_days,
                percentile=percentile,
                min_price=min_price,
                limit=limit
            )
            
            self.write({
                "code": 200,
                "msg": "success",
                "data": {
                    "stocks": result,
                    "total": len(result)
                }
            })
        except ValueError as e:
            self.set_status(400)
            self.write({
                "code": 400,
                "msg": f"参数错误: {str(e)}",
                "data": {}
            })
        except Exception as e:
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": f"历史低位分析失败: {str(e)}",
                "data": {}
            })


# 路由注册函数
def add_stock_selector_handlers(app):
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    tushare_token = os.getenv('TUSHARE_TOKEN')
    selector = StockSelector(tushare_token=tushare_token)
    
    app.add_handlers(r".*", [
        (r"/api/stock/select", StockSelectHandler, {"selector": selector}),
        (r"/api/stock/sector-risk", SectorRiskHandler, {"selector": selector}),
        (r"/api/stock/historical-low", HistoricalLowHandler, {"selector": selector}),
    ])
    print("选股API路由已注册:")
    print("  - GET/POST /api/stock/select 支持wencai参数")
    print("  - GET /api/stock/sector-risk 板块风险分析")
    print("  - GET /api/stock/historical-low 历史低位股票查询") 