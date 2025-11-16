from modules.tornadoapp.controller.position_handler import PositionAnalysisHandler, PositionDetailHandler, PositionReportHandler
from modules.tornadoapp.controller.technical_analysis_handler import TechnicalAnalysisHandler, TradingSignalHandler, IndicatorAnalysisHandler

def add_position_handlers(app):
    """添加持仓分析和技术分析相关的路由"""
    
    # 持仓分析API
    app.add_handlers(r".*", [
        (r"/api/position/analysis", PositionAnalysisHandler),
        (r"/api/position/detail", PositionDetailHandler),
        (r"/api/position/report", PositionReportHandler),
        
        # 技术分析API
        (r"/api/technical/analysis", TechnicalAnalysisHandler),
        (r"/api/technical/signals", TradingSignalHandler),
        (r"/api/technical/indicators", IndicatorAnalysisHandler),
    ])
