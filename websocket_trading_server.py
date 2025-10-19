#!/usr/bin/env python3
"""
量化交易WebSocket服务器
支持实时行情、订单状态、交易信号推送

作者: AI Assistant
创建时间: 2025-01-15
版本: 1.0
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Dict, List, Set
from datetime import datetime
import pandas as pd
from database.market_data_manager import MarketDataManager

app = FastAPI(title="量化交易WebSocket服务器")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # 用户订阅的股票
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        logging.info(f"客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        logging.info(f"客户端 {client_id} 已断开")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast_to_subscribers(self, message: str, symbol: str):
        """向订阅特定股票的用户广播消息"""
        for client_id, subscriptions in self.subscriptions.items():
            if symbol in subscriptions:
                await self.send_personal_message(message, client_id)
    
    def subscribe_stock(self, client_id: str, symbol: str):
        """订阅股票"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].add(symbol)
            logging.info(f"客户端 {client_id} 订阅股票 {symbol}")
    
    def unsubscribe_stock(self, client_id: str, symbol: str):
        """取消订阅股票"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(symbol)
            logging.info(f"客户端 {client_id} 取消订阅股票 {symbol}")

manager = ConnectionManager()
data_manager = MarketDataManager()

# WebSocket端点
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            if message['type'] == 'subscribe':
                symbol = message['symbol']
                manager.subscribe_stock(client_id, symbol)
                
                # 发送确认消息
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'subscription_confirmed',
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat()
                    }),
                    client_id
                )
            
            elif message['type'] == 'unsubscribe':
                symbol = message['symbol']
                manager.unsubscribe_stock(client_id, symbol)
                
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'unsubscription_confirmed',
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat()
                    }),
                    client_id
                )
            
            elif message['type'] == 'ping':
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }),
                    client_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# 模拟实时数据推送
class RealTimeDataSimulator:
    def __init__(self):
        self.running = False
    
    async def start_simulation(self):
        """启动实时数据模拟"""
        self.running = True
        
        # 模拟股票列表
        stocks = ['000001.SZ', '000002.SZ', '600519.SH', '600036.SH']
        
        while self.running:
            for symbol in stocks:
                # 模拟tick数据
                tick_data = {
                    'type': 'tick',
                    'symbol': symbol,
                    'price': round(10 + (hash(symbol + str(datetime.now())) % 100) / 10, 2),
                    'volume': (hash(symbol + str(datetime.now())) % 10000) + 1000,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 广播给订阅用户
                await manager.broadcast_to_subscribers(
                    json.dumps(tick_data),
                    symbol
                )
            
            await asyncio.sleep(1)  # 每秒推送一次
    
    def stop_simulation(self):
        """停止模拟"""
        self.running = False

# 启动实时数据模拟
simulator = RealTimeDataSimulator()

@app.on_event("startup")
async def startup_event():
    """应用启动时启动数据模拟"""
    asyncio.create_task(simulator.start_simulation())

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止数据模拟"""
    simulator.stop_simulation()

# HTTP API端点
@app.get("/api/stocks")
async def get_stocks():
    """获取股票列表"""
    stocks = data_manager.get_stock_list()
    return {"stocks": stocks}

@app.get("/api/data/{symbol}")
async def get_stock_data(symbol: str, start_date: str, end_date: str):
    """获取历史数据"""
    data = data_manager.get_daily_data(symbol, start_date, end_date)
    return {
        "symbol": symbol,
        "data": data.to_dict('records'),
        "count": len(data)
    }

@app.get("/api/indicators/{symbol}")
async def get_technical_indicators(symbol: str, start_date: str, end_date: str):
    """获取技术指标"""
    indicators = data_manager.get_technical_indicators(symbol, start_date, end_date)
    return indicators.to_dict('records')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

