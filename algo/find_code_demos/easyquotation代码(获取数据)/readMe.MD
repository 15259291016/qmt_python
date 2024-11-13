新浪 ['sina'] 腾讯 ['tencent', 'qq'] 
import easyquotation

quotation = easyquotation.use('sina') # 新浪 ['sina'] 腾讯 ['tencent', 'qq'] 

#获取所有股票行情
quotation.market_snapshot(prefix=True) # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀

#单只股票
quotation.real('162411') # 支持直接指定前缀，如 'sh000001'

#多只股票
quotation.stocks(['000001', '162411']) 

#同时获取指数和行情
quotation.stocks(['sh000001', 'sz000001'], prefix=True)

作者：叶公
链接：https://www.zhihu.com/question/438404653/answer/1667090443
来源：知乎
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。