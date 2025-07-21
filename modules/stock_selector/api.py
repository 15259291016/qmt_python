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

# 路由注册函数
def add_stock_selector_handlers(app):
    selector = StockSelector()
    app.add_handlers(r".*", [
        (r"/api/stock/select", StockSelectHandler, {"selector": selector}),
    ])
    print("选股API路由已注册: GET/POST /api/stock/select 支持wencai参数") 