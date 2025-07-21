import pandas as pd
from typing import List, Optional, Dict, Any

class StockSelector:
    """
    标准选股服务，支持多条件筛选和pywencai智能选股。
    """
    def __init__(self, data_source=None):
        self.data_source = data_source

    def select(
        self,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = None,
        min_mv: Optional[float] = None,
        max_mv: Optional[float] = None,
        industry: Optional[str] = None,
        min_change: Optional[float] = None,
        max_change: Optional[float] = None,
        ma_cross: Optional[Dict[str, int]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        df = self.data_source.get_all_stocks()
        if min_pe is not None:
            df = df[df['pe'] >= min_pe]
        if max_pe is not None:
            df = df[df['pe'] <= max_pe]
        if min_mv is not None:
            df = df[df['market_value'] >= min_mv]
        if max_mv is not None:
            df = df[df['market_value'] <= max_mv]
        if industry:
            df = df[df['industry'] == industry]
        if min_change is not None:
            df = df[df['pct_chg'] >= min_change]
        if max_change is not None:
            df = df[df['pct_chg'] <= max_change]
        if ma_cross:
            short = ma_cross.get('short', 5)
            long = ma_cross.get('long', 20)
            if f'ma{short}' in df.columns and f'ma{long}' in df.columns:
                df = df[df[f'ma{short}'] > df[f'ma{long}']]
        result = df[['symbol', 'name', 'industry', 'pe', 'market_value', 'pct_chg']].head(limit)
        return result.to_dict(orient='records')

    def select_by_wencai(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """用pywencai智能选股"""
        try:
            import pywencai
        except ImportError:
            raise RuntimeError("请先安装 pywencai: pip install pywencai")
        df = pywencai.get(query = query)
        if df is None or df.empty:
            return []
        # 兼容不同字段名
        code_col = 'code' if 'code' in df.columns else '股票代码'
        name_col = 'name' if 'name' in df.columns else '股票简称'
        result = df[[code_col, name_col]].head(limit)
        result = result.rename(columns={code_col: 'symbol', name_col: 'name'})
        return result.to_dict(orient='records') 