'''
Date: 2024-03-21 16:11:02
LastEditors: 牛智超
LastEditTime: 2024-08-23 13:58:23
FilePath: \app\api\endpoints\stock_strategy.py
'''
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from pydantic import BaseModel
from typing import Union, List, Optional
from fastapi.responses import FileResponse
# from dependencies import get_token_header
import qstock as qs
import pandas as pd
import os
import easyquotation
from pathlib import Path
from sqlalchemy import text
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from sqlalchemy import and_

from app.db import pgsql
from app.db.pgsql import tjItem, WatchCode, WaitBuyList

import easyquotation

from app.util.utils import gp_type_szsh
import pywencai as wc
from sqlalchemy.exc import IntegrityError

from algo.app.db.pgsql import RecordOfTotalTurnover

quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

router = APIRouter(
    prefix="",
    tags=["stock_strategy"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


class OrdersItem(BaseModel):
    m_strInstrumentID: str  # 证券代码
    m_strInstrumentName: str  # 证券名称
    m_nOffsetFlag: int  # 买卖方向
    m_nVolumeTotalOriginal: int  # 委托数量
    m_dTradedPrice: float  # 成交价格
    m_nVolumeTraded: int  # 成交数量
    m_dTradeAmount: float  # 成交金额


class DealsItem(BaseModel):
    m_strInstrumentID: str  # 证券代码
    m_strInstrumentName: str  # 证券名称
    m_nOffsetFlag: int  # 买卖方向
    m_dPrice: float  # 成交价格
    m_nVolume: int  # 成交数量
    m_dTradeAmount: float  # 成交金额


class PositionsItem(BaseModel):
    m_strInstrumentID: str  # 证券代码
    m_strInstrumentName: str  # 证券名称
    m_nVolume: int  # 持仓数量
    m_nCanUseVolume: int  # 可用数量
    m_dOpenPrice: float  # 开仓价格
    m_dInstrumentValue: float  # 证券市值
    m_dPositionCost: float  # 持仓成本
    m_dPositionProfit: float  # 盈亏


class AccountsItem(BaseModel):
    m_dBalance: float  # 账户余额
    m_dAssureAsset: float  # 总资产
    m_dInstrumentValue: float  # 证券市值
    m_dAvailable: float  # 可用资金
    m_dPositionProfit: float  # 持仓盈亏


class SellItem(BaseModel):
    current_amount: float
    northbound_inflow: float
    northbound_outflow: float
    all: float
    orders: List[OrdersItem]
    deals: List[DealsItem]
    positions: List[PositionsItem]
    accounts: List[AccountsItem]


@router.get("/")
def read_root():
    print('read_root')
    return {"Hello": "World"}


@router.post("/init")
async def init(request: Request):
    print('init-----------------------------------------')
    return {"data": "今日无推荐", "code": 1,
            }


@router.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@router.post("/login")
def login(request: Request):
    item_json = request.json()
    return {"Hello": "World"}


@router.post("/sell")
async def sell(request: SellItem):
    """
    分阶段卖出
    可以借鉴AI分时高低策略，
    不能猛砸，有大单就出给大单，有小单就出给小单
    """

    return_res = {"result": "False"}

    account = {
        "now_hold_stock_code": '',
        "now_hold_stock_name": '',
        "now_hold_stock_num": '',
    }

    orders, deals, positions, accounts = request.orders, request.deals, request.positions, request.accounts
    # 订单
    for o in orders:
        m_strInstrumentID = o.m_strInstrumentID
        m_strInstrumentName = o.m_strInstrumentName
        m_nOffsetFlag = o.m_nOffsetFlag
        m_nVolumeTotalOriginal = o.m_nVolumeTotalOriginal
        m_dTradedPrice = o.m_dTradedPrice
        m_nVolumeTraded = o.m_nVolumeTraded
        m_dTradeAmount = o.m_dTradeAmount
    for d in deals:
        m_strInstrumentID = d.m_strInstrumentID
        m_strInstrumentName = d.m_strInstrumentName
        m_nOffsetFlag = d.m_nOffsetFlag
        m_dPrice = d.m_dPrice
        m_nVolume = d.m_nVolume
        m_dTradeAmount = d.m_dTradeAmount
    for p in positions:
        m_strInstrumentID = p.m_strInstrumentID
        m_strInstrumentName = p.m_strInstrumentName
        m_nVolume = p.m_nVolume
        if m_nVolume > 0:
            account['now_hold_stock_code'] = m_strInstrumentID
            account['now_hold_stock_name'] = m_strInstrumentName
            account['now_hold_stock_num'] = m_nVolume
        m_nCanUseVolume = p.m_nCanUseVolume
        m_dOpenPrice = p.m_dOpenPrice
        m_dInstrumentValue = p.m_dInstrumentValue
        m_dPositionCost = p.m_dPositionCost
        m_dPositionProfit = p.m_dPositionProfit

    for a in accounts:
        account['m_dBalance'] = a.m_dBalance
        account['m_dAssureAsset'] = a.m_dAssureAsset
        account['m_dInstrumentValue'] = a.m_dInstrumentValue
        account['m_dAvailable'] = a.m_dAvailable
        account['m_dPositionProfit'] = a.m_dPositionProfit
    profit = float(account['m_dPositionProfit'])
    pgsql.add_record(round(request.current_amount/10000/10000),round(request.northbound_inflow,2),round(request.northbound_outflow,2),round(request.all,2))
    # if float(profit) / account['m_dBalance'] > 0.03 or float(profit) / account['m_dBalance'] < -0.1:
    #     return_res = {"result": "True"}
    # 计算是否卖出
    if len(positions) == 0:
        return return_res
    try:
        code = [i for i in [gp_type_szsh(positions[0].m_strInstrumentID).split(".")[1].lower() + gp_type_szsh(positions[0].m_strInstrumentID).split(".")[0]]]
    except Exception as e:
        code = positions[0].m_strInstrumentID
        print(e)
    # info_set = quotation.stocks(gp_type_szsh(positions[0].m_strInstrumentID), prefix=True)
    info_set = quotation.stocks(code, prefix=True)

    return return_res

@router.get("/get_data")
async def get_data():
    all_info = pd.DataFrame(quotation.market_snapshot(prefix=True).values())
    # >2000亿 总量
    sz_gt2000 = len(all_info[all_info['总市值'] >= 2000])
    # >2000亿 10%数量
    sz_gt2000_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] >= 2000)])
    # >2000亿 10%数量 比例
    sz_gt2000_zd_gt10_ratio = sz_gt2000_zd_gt10 / sz_gt2000
    # >2000亿 3%-7%数量
    sz_gt2000_zd_gt3lt7 = len(
        all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 2000)])
    # sz_gt2000_zd_gt10 比例
    sz_gt2000_zd_gt3lt7_ratio = sz_gt2000_zd_gt3lt7 / sz_gt2000
    # >2000亿 0%--3%数量
    sz_gt2000_zd_gt0lt3 = len(
        all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 2000)])
    # >2000亿 0%--3%数量 比例
    sz_gt2000_zd_gt0lt3_ratio = sz_gt2000_zd_gt0lt3 / sz_gt2000
    # >2000亿 -3%-0%%数量
    sz_gt2000_zd_gt_3lt0 = len(
        all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] < 0) & (all_info['总市值'] >= 2000)])
    # >2000亿 -3%-0%%数量 比例
    sz_gt2000_zd_gt_3lt0_ratio = sz_gt2000_zd_gt_3lt0 / sz_gt2000
    # >2000亿 -7%-3%数量
    sz_gt2000_zd_gt_7lt_3 = len(
        all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 2000)])
    # >2000亿 -7%-3%数量 比例
    sz_gt2000_zd_gt_7lt_3_ratio = sz_gt2000_zd_gt_7lt_3 / sz_gt2000
    # >2000亿 -10%-7%数量
    sz_gt2000_zd_gt_7lt_10 = len(
        all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 2000)])
    # >2000亿 -10%-7%数量 比例
    sz_gt2000_zd_gt_7lt_10_ratio = sz_gt2000_zd_gt_7lt_10 / sz_gt2000
    # >2000亿 -10%%数量
    sz_gt2000_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] >= 2000)])
    # >2000亿 -10%%数量 比例
    sz_gt2000_zd_lt_10_ratio = sz_gt2000_zd_lt_10 / sz_gt2000
    # >1000亿 总量
    sz_gt1000 = len(all_info[(all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 10%数量
    sz_gt1000_zd_gt10 = len(
        all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 10%数量 比例
    sz_gt1000_zd_gt10_ratio = sz_gt1000_zd_gt10 / sz_gt1000
    # >1000亿 7%--3%数量
    sz_gt1000_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (
                all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 7%--3%数量 比例
    sz_gt1000_zd_lt7gt3_ratio = sz_gt1000_zd_lt7gt3 / sz_gt1000
    # >1000亿 0%--3%数量
    sz_gt1000_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (
                all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 0%--3%数量 比例
    sz_gt1000_zd_gt0lt3_ratio = sz_gt1000_zd_gt0lt3 / sz_gt1000
    # >1000亿 -3%-0%%数量
    sz_gt1000_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] < 0) & (
                all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -3%-0%%数量 比例
    sz_gt1000_zd_gt_3lt0_ratio = sz_gt1000_zd_gt_3lt0 / sz_gt1000
    # >1000亿 -7%-3%数量
    sz_gt1000_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (
                all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -7%-3%数量 比例
    sz_gt1000_zd_gt_7lt_3_ratio = sz_gt1000_zd_gt_7lt_3 / sz_gt1000
    # >1000亿 -10%-7%数量
    sz_gt1000_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (
                all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -10%-7%数量 比例
    sz_gt1000_zd_gt_7lt_10_ratio = sz_gt1000_zd_gt_7lt_10 / sz_gt1000
    # >1000亿 -10%%数量
    sz_gt1000_zd_lt_10 = len(
        all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -10%%数量 比例
    sz_gt1000_zd_lt_10_ratio = sz_gt1000_zd_lt_10 / sz_gt1000
    # >500亿 总量
    sz_gt500 = len(all_info[(all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 10%数量
    sz_gt500_zd_gt10 = len(
        all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 10%数量 比例
    sz_gt500_zd_gt10_ratio = sz_gt500_zd_gt10 / sz_gt500
    # >500亿 7%--3%数量
    sz_gt500_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (
                all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 7%--3%数量 比例
    sz_gt500_zd_lt7gt3_ratio = sz_gt500_zd_lt7gt3 / sz_gt500
    # >500亿 0%--3%数量
    sz_gt500_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (
                all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 0%--3%数量 比例
    sz_gt500_zd_gt0lt3_ratio = sz_gt500_zd_gt0lt3 / sz_gt500
    # >500亿 -3%-0%%数量
    sz_gt500_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] < 0) & (
                all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -3%-0%%数量 比例
    sz_gt500_zd_gt_3lt0_ratio = sz_gt500_zd_gt_3lt0 / sz_gt500
    # >500亿 -7%-3%数量
    sz_gt500_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (
                all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -7%-3%数量 比例
    sz_gt500_zd_gt_7lt_3_ratio = sz_gt500_zd_gt_7lt_3 / sz_gt500
    # >500亿 -10%-7%数量
    sz_gt500_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (
                all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -10%-7%数量 比例
    sz_gt500_zd_gt_7lt_10_ratio = sz_gt500_zd_gt_7lt_10 / sz_gt500
    # >500亿 -10%%数量
    sz_gt500_zd_lt_10 = len(
        all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -10%%数量 比例
    sz_gt500_zd_lt_10_ratio = sz_gt500_zd_lt_10 / sz_gt500
    # >100亿 总量
    sz_gt100 = len(all_info[all_info['总市值'] >= 100])
    # >100亿 10%数量
    sz_gt100_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] >= 100)])
    # >100亿 10%数量 比例
    sz_gt100_zd_gt10_ratio = sz_gt100_zd_gt10 / sz_gt100
    # >100亿 3%-7%数量
    sz_gt100_zd_gt3lt7 = len(
        all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 100)])
    # >100亿 3%-7%数量 比例
    sz_gt100_zd_gt3lt7_ratio = sz_gt100_zd_gt3lt7 / sz_gt100
    # >100亿 0%--3%数量
    sz_gt100_zd_gt0lt3 = len(
        all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 100)])
    # >100亿 0%--3%数量 比例
    sz_gt100_zd_gt0lt3_ratio = sz_gt100_zd_gt0lt3 / sz_gt100
    # >100亿 -3%-0%%数量
    sz_gt100_zd_gt_3lt0 = len(
        all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] < 0) & (all_info['总市值'] >= 100)])
    # >100亿 -3%-0%%数量 比例
    sz_gt100_zd_gt_3lt0_ratio = sz_gt100_zd_gt_3lt0 / sz_gt100
    # >100亿 -7%-3%数量
    sz_gt100_zd_gt_7lt_3 = len(
        all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 100)])
    # >100亿 -7%-3%数量 比例
    sz_gt100_zd_gt_7lt_3_ratio = sz_gt100_zd_gt_7lt_3 / sz_gt100
    # >100亿 -10%-7%数量
    sz_gt100_zd_gt_7lt_10 = len(
        all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 100)])
    # >100亿 -10%-7%数量 比例
    sz_gt100_zd_gt_7lt_10_ratio = sz_gt100_zd_gt_7lt_10 / sz_gt100
    # >100亿 -10%%数量
    sz_gt100_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] >= 100)])
    # >100亿 -10%%数量 比例
    sz_gt100_zd_lt_10_ratio = sz_gt100_zd_lt_10 / sz_gt100
    # 50-100亿 总量
    sz_gt50lt100 = len(all_info[(all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
    # 50-100亿 10%数量
    sz_gt50lt100_zd_gt10 = len(
        all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
    # 50-100亿 10%数量 比例
    sz_gt50lt100_zd_gt10_ratio = sz_gt50lt100_zd_gt10 / sz_gt50lt100
    # 50-100亿 7%--3%数量
    sz_gt50lt100_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (
                all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 7%--3%数量 比例
    sz_gt50lt100_zd_lt7gt3_ratio = sz_gt50lt100_zd_lt7gt3 / sz_gt50lt100
    # 50-100亿 0%--3%数量
    sz_gt50lt100_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (
                all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 0%--3%数量 比例
    sz_gt50lt100_zd_gt0lt3_ratio = sz_gt50lt100_zd_gt0lt3 / sz_gt50lt100
    # 50-100亿 -3%-0%%数量
    sz_gt50lt100_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] < 0) & (
                all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -3%-0%%数量 比例
    sz_gt50lt100_zd_gt_3lt0_ratio = sz_gt50lt100_zd_gt_3lt0 / sz_gt50lt100
    # 50-100亿 -7%-3%数量
    sz_gt50lt100_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (
                all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -7%-3%数量 比例
    sz_gt50lt100_zd_gt_7lt_3_ratio = sz_gt50lt100_zd_gt_7lt_3 / sz_gt50lt100
    # 50-100亿 -10%-7%数量
    sz_gt50lt100_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (
                all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -10%-7%数量 比例
    sz_gt50lt100_zd_gt_7lt_10_ratio = sz_gt50lt100_zd_gt_7lt_10 / sz_gt50lt100
    # 50-100亿 -10%%数量
    sz_gt50lt100_zd_lt_10 = len(
        all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] > 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -10%%数量 比例
    sz_gt50lt100_zd_lt_10_ratio = sz_gt50lt100_zd_lt_10 / sz_gt50lt100
    # <50亿 总量
    sz_lt50 = len(all_info[all_info['总市值'] < 50])
    # <50亿 10%数量
    sz_lt50_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] <= 50)])
    # <50亿 10%数量 比例
    sz_lt50_zd_gt10_ratio = sz_lt50_zd_gt10 / sz_lt50

    # <50亿 7%--3%数量
    sz_lt50_zd_lt7gt3 = len(
        all_info[(all_info['涨跌(%)'] > 3) & (all_info['涨跌(%)'] < 7) & (all_info['总市值'] < 50)])
    # <50亿 7%--3%数量 比例
    sz_lt50_zd_lt7gt3_ratio = sz_lt50_zd_lt7gt3 / sz_lt50
    # <50亿 0%--3%数量
    sz_lt50_zd_gt0lt3 = len(
        all_info[(all_info['涨跌(%)'] > 0) & (all_info['涨跌(%)'] < 3) & (all_info['总市值'] < 50)])
    # <50亿 0%--3%数量 比例
    sz_lt50_zd_gt0lt3_ratio = sz_lt50_zd_gt0lt3 / sz_lt50
    # <50亿 -3%-0%%数量
    sz_lt50_zd_gt_3lt0 = len(
        all_info[(all_info['涨跌(%)'] > -3) & (all_info['涨跌(%)'] < 0) & (all_info['总市值'] < 50)])
    # <50亿 -3%-0%%数量 比例
    sz_lt50_zd_gt_3lt0_ratio = sz_lt50_zd_gt_3lt0 / sz_lt50
    # <50亿 -7%-3%数量
    sz_lt50_zd_gt_7lt_3 = len(
        all_info[(all_info['涨跌(%)'] > -7) & (all_info['涨跌(%)'] < -3) & (all_info['总市值'] < 50)])
    # <50亿 -7%-3%数量 比例
    sz_lt50_zd_gt_7lt_3_ratio = sz_lt50_zd_gt_7lt_3 / sz_lt50
    # <50亿 -10%-7%数量
    sz_lt50_zd_gt_7lt_10 = len(
        all_info[(all_info['涨跌(%)'] > -10) & (all_info['涨跌(%)'] < -7) & (all_info['总市值'] < 50)])
    # <50亿 -10%-7%数量 比例
    sz_lt50_zd_gt_7lt_10_ratio = sz_lt50_zd_gt_7lt_10 / sz_lt50
    # <50亿 -10%%数量
    sz_lt50_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] < 50)])
    # <50亿 -10%%数量 比例
    sz_lt50_zd_lt_10_ratio = sz_lt50_zd_lt_10 / sz_lt50
    # >100亿 5%数量
    sz_gt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] > 100)])
    # >100亿 5%数量 比例
    sz_gt100_zd_gt5_ratio = sz_gt100_zd_gt5 / sz_gt100
    # 50-100亿 5%数量
    sz_gt50lt100_zd_gt5 = len(
        all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 100) & (all_info['总市值'] > 50)])
    # 50-100亿 5%数量 比例
    sz_gt50lt100_zd_gt5_ratio = sz_gt50lt100_zd_gt5 / sz_gt50lt100
    # <50亿 5%数量
    sz_lt50_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 50)])
    # <50亿 5%数量 比例
    sz_lt50_zd_gt5_ratio = sz_lt50_zd_gt5 / sz_lt50
    # >10% 数量
    zd_gt10 = len(all_info[all_info['涨跌(%)'] > 10])
    # >10% 数量 比例
    zd_gt10_ratio = zd_gt10 / len(all_info)
    # >5% 数量
    zd_gt5 = len(all_info[all_info['涨跌(%)'] > 5])
    # >5% 数量 比例
    zd_gt5_ratio = zd_gt5 / len(all_info)
    # >3% 数量
    zd_gt3 = len(all_info[all_info['涨跌(%)'] > 3])
    # >3% 数量 比例
    zd_gt3_ratio = zd_gt3 / len(all_info)

    # ---------------------盘后--------------------------------
    # 5日 涨超5%数量
    # res = wc.get(query='5日涨幅超过5%')
    # # 5日 涨超10%数量
    # res = wc.get(query='5日涨幅超过10%')
    # # 跌超 10%数量
    # zd_lt10 = all_info[all_info['涨跌(%)'] < -10]
    return {
        ">2000亿 总量": sz_gt2000,  # >2000亿 总量
        ">2000亿 10%数量": sz_gt2000_zd_gt10,  # >2000亿 10%数量
        ">2000亿 10%数量 比例": sz_gt2000_zd_gt10_ratio,  # >2000亿 10%数量 比例
        ">2000亿 3%-7%数量": sz_gt2000_zd_gt3lt7,  # >2000亿 3%-7%数量
        ">2000亿 3%-7%数量 比例": sz_gt2000_zd_gt3lt7_ratio,  # >2000亿 3%-7%数量 比例
        ">2000亿 0%--3%数量": sz_gt2000_zd_gt0lt3,  # >2000亿 0%--3%数量
        ">2000亿 0%--3%数量 比例": sz_gt2000_zd_gt0lt3_ratio,  # >2000亿 0%--3%数量 比例
        ">2000亿 -3%-0%%数量": sz_gt2000_zd_gt_3lt0,  # >2000亿 -3%-0%%数量
        ">2000亿 -3%-0%%数量 比例": sz_gt2000_zd_gt_3lt0_ratio,  # >2000亿 -3%-0%%数量 比例
        ">2000亿 -7%-3%数量": sz_gt2000_zd_gt_7lt_3,  # >2000亿 -7%-3%数量
        ">2000亿 -7%-3%数量 比例": sz_gt2000_zd_gt_7lt_3_ratio,  # >2000亿 -7%-3%数量 比例
        ">2000亿 -10%-7%数量": sz_gt2000_zd_gt_7lt_10,  # >2000亿 -10%-7%数量
        ">2000亿 -10%-7%数量 比例": sz_gt2000_zd_gt_7lt_10_ratio,  # >2000亿 -10%-7%数量 比例
        ">2000亿 -10%%数量": sz_gt2000_zd_lt_10,  # >2000亿 -10%%数量
        ">2000亿 -10%%数量 比例": sz_gt2000_zd_lt_10_ratio,  # >2000亿 -10%%数量 比例
        ">1000亿 总量": sz_gt1000,  # >1000亿 总量
        ">1000亿 10%数量": sz_gt1000_zd_gt10,  # >1000亿 10%数量
        ">1000亿 10% 比例": sz_gt1000_zd_gt10_ratio,  # >1000亿 10%数量 比例
        ">1000亿 7%--3%数量": sz_gt1000_zd_lt7gt3,  # >1000亿 7%--3%数量
        ">1000亿 7%--3%数量 比例": sz_gt1000_zd_lt7gt3_ratio,  # >1000亿 7%--3%数量 比例
        ">1000亿 0%--3%数量": sz_gt1000_zd_gt0lt3,  # >1000亿 0%--3%数量
        ">1000亿 0%--3%数量 比例": sz_gt1000_zd_gt0lt3_ratio,  # >1000亿 0%--3%数量 比例
        ">1000亿 -3%-0%%数量": sz_gt1000_zd_gt_3lt0,  # >1000亿 -3%-0%%数量
        ">1000亿 -3%-0%%数量 比例": sz_gt1000_zd_gt_3lt0_ratio,  # >1000亿 -3%-0%%数量 比例
        ">1000亿 -7%-3%数量": sz_gt1000_zd_gt_7lt_3,  # >1000亿 -7%-3%数量
        ">1000亿 -7%-3%数量 比例": sz_gt1000_zd_gt_7lt_3_ratio,  # >1000亿 -7%-3%数量 比例
        ">1000亿 -10%-7%数量": sz_gt1000_zd_gt_7lt_10,  # >1000亿 -10%-7%数量
        ">1000亿 -10%-7%数量 比例": sz_gt1000_zd_gt_7lt_10_ratio,  # >1000亿 -10%-7%数量 比例
        ">1000亿 -10%%数量": sz_gt1000_zd_lt_10,  # >1000亿 -10%%数量
        ">1000亿 -10%%数量 比例": sz_gt1000_zd_lt_10_ratio,  # >1000亿 -10%%数量 比例
        ">500亿 总量": sz_gt500,  # >500亿 总量
        ">500亿 10%数量": sz_gt500_zd_gt10,  # >500亿 10%数量
        ">500亿 10%数量 比例": sz_gt500_zd_gt10_ratio,  # >500亿 10%数量 比例
        ">500亿 7%--3%数量": sz_gt500_zd_lt7gt3,  # >500亿 7%--3%数量
        ">500亿 7%--3%数量 比例": sz_gt500_zd_lt7gt3_ratio,  # >500亿 7%--3%数量 比例
        ">500亿 0%--3%数量": sz_gt500_zd_gt0lt3,  # >500亿 0%--3%数量
        ">500亿 0%--3%数量 比例": sz_gt500_zd_gt0lt3_ratio,  # >500亿 0%--3%数量 比例
        ">500亿 -3%-0%%数量": sz_gt500_zd_gt_3lt0,  # >500亿 -3%-0%%数量
        ">500亿 -3%-0%%数量 比例": sz_gt500_zd_gt_3lt0_ratio,  # >500亿 -3%-0%%数量 比例
        ">500亿 -7%-3%数量": sz_gt500_zd_gt_7lt_3,  # >500亿 -7%-3%数量
        ">500亿 -7%-3%数量 比例": sz_gt500_zd_gt_7lt_3_ratio,  # >500亿 -7%-3%数量 比例
        ">500亿 -10%-7%数量": sz_gt500_zd_gt_7lt_10,  # >500亿 -10%-7%数量
        ">500亿 -10%-7%数量 比例": sz_gt500_zd_gt_7lt_10_ratio,  # >500亿 -10%-7%数量 比例
        ">500亿 -10%%数量": sz_gt500_zd_lt_10,  # >500亿 -10%%数量
        ">500亿 -10%%数量 比例": sz_gt500_zd_lt_10_ratio,  # >500亿 -10%%数量 比例
        ">100亿 总量": sz_gt100,  # >100亿 总量
        ">100亿 10%数量": sz_gt100_zd_gt10,  # >100亿 10%数量
        ">100亿 10%数量 比例": sz_gt100_zd_gt10_ratio,  # >100亿 10%数量 比例
        ">100亿 3%-7%数量": sz_gt100_zd_gt3lt7,  # >100亿 3%-7%数量
        ">100亿 3%-7%数量 比例": sz_gt100_zd_gt3lt7_ratio,  # >100亿 3%-7%数量 比例
        ">100亿 0%--3%数量": sz_gt100_zd_gt0lt3,  # >100亿 0%--3%数量
        ">100亿 0%--3%数量 比例": sz_gt100_zd_gt0lt3_ratio,  # >100亿 0%--3%数量 比例
        ">100亿 -3%-0%%数量": sz_gt100_zd_gt_3lt0,  # >100亿 -3%-0%%数量
        ">100亿 -3%-0%%数量 比例": sz_gt100_zd_gt_3lt0_ratio,  # >100亿 -3%-0%%数量 比例
        ">100亿 -7%-3%数量": sz_gt100_zd_gt_7lt_3,  # >100亿 -7%-3%数量
        ">100亿 -7%-3%数量 比例": sz_gt100_zd_gt_7lt_3_ratio,  # >100亿 -7%-3%数量 比例
        ">100亿 -10%-7%数量": sz_gt100_zd_gt_7lt_10,  # >100亿 -10%-7%数量
        ">100亿 -10%-7%数量 比例": sz_gt100_zd_gt_7lt_10_ratio,  # >100亿 -10%-7%数量 比例
        ">100亿 -10%%数量": sz_gt100_zd_lt_10,  # >100亿 -10%%数量
        ">100亿 -10%%数量 比例": sz_gt100_zd_lt_10_ratio,  # >100亿 -10%%数量 比例
        "50-100亿 总量": sz_gt50lt100,  # 50-100亿 总量
        "50-100亿 10%数量": sz_gt50lt100_zd_gt10,  # 50-100亿 10%数量
        "50-100亿 10%数量 比例": sz_gt50lt100_zd_gt10_ratio,  # 50-100亿 10%数量 比例
        "50-100亿 7%--3%数量": sz_gt50lt100_zd_lt7gt3,  # 50-100亿 7%--3%数量
        "50-100亿 7%--3%数量 比例": sz_gt50lt100_zd_lt7gt3_ratio,  # 50-100亿 7%--3%数量 比例
        "50-100亿 0%--3%数量": sz_gt50lt100_zd_gt0lt3,  # 50-100亿 0%--3%数量
        "50-100亿 0%--3%数量 比例": sz_gt50lt100_zd_gt0lt3_ratio,  # 50-100亿 0%--3%数量 比例
        "50-100亿 -3%-0%%数量": sz_gt50lt100_zd_gt_3lt0,  # 50-100亿 -3%-0%%数量
        "50-100亿 -3%-0%%数量 比例": sz_gt50lt100_zd_gt_3lt0_ratio,  # 50-100亿 -3%-0%%数量 比例
        "50-100亿 -7%-3%数量": sz_gt50lt100_zd_gt_7lt_3,  # 50-100亿 -7%-3%数量
        "50-100亿 -7%-3%数量 比例": sz_gt50lt100_zd_gt_7lt_3_ratio,  # 50-100亿 -7%-3%数量 比例
        "50-100亿 -10%-7%数量": sz_gt50lt100_zd_gt_7lt_10,  # 50-100亿 -10%-7%数量
        "50-100亿 -10%-7%数量 比例": sz_gt50lt100_zd_gt_7lt_10_ratio,  # 50-100亿 -10%-7%数量 比例
        "50-100亿 -10%%数量": sz_gt50lt100_zd_lt_10,  # 50-100亿 -10%%数量
        "50-100亿 -10%%数量 比例": sz_gt50lt100_zd_lt_10_ratio,  # 50-100亿 -10%%数量 比例
        "<50亿 总量": sz_lt50,  # <50亿 总量
        "<50亿 10%数量": sz_lt50_zd_gt10,  # <50亿 10%数量
        "<50亿 10%数量 比例": sz_lt50_zd_gt10_ratio,  # <50亿 10%数量 比例
        "<50亿 7%--3%数量": sz_lt50_zd_lt7gt3,  # <50亿 7%--3%数量
        "<50亿 7%--3%数量 比例": sz_lt50_zd_lt7gt3_ratio,  # <50亿 7%--3%数量 比例
        "<50亿 0%--3%数量": sz_lt50_zd_gt0lt3,  # <50亿 0%--3%数量
        "<50亿 0%--3%数量 比例": sz_lt50_zd_gt0lt3_ratio,  # <50亿 0%--3%数量 比例
        "<50亿 -3%-0%%数量": sz_lt50_zd_gt_3lt0,  # <50亿 -3%-0%%数量
        "<50亿 -3%-0%%数量 比例": sz_lt50_zd_gt_3lt0_ratio,  # <50亿 -3%-0%%数量 比例
        "<50亿 -7%-3%数量": sz_lt50_zd_gt_7lt_3,  # <50亿 -7%-3%数量
        "<50亿 -7%-3%数量 比例": sz_lt50_zd_gt_7lt_3_ratio,  # <50亿 -7%-3%数量 比例
        "<50亿 -10%-7%数量": sz_lt50_zd_gt_7lt_10,  # <50亿 -10%-7%数量
        "<50亿 -10%-7%数量 比例": sz_lt50_zd_gt_7lt_10_ratio,  # <50亿 -10%-7%数量 比例
        "<50亿 -10%%数量": sz_lt50_zd_lt_10,  # <50亿 -10%%数量
        "<50亿 -10%%数量 比例": sz_lt50_zd_lt_10_ratio,  # <50亿 -10%%数量 比例
        ">100亿 5%数量": sz_gt100_zd_gt5,  # >100亿 5%数量
        ">100亿 5%数量 比例": sz_gt100_zd_gt5_ratio,  # >100亿 5%数量 比例
        "50-100亿 5%数量": sz_gt50lt100_zd_gt5,  # 50-100亿 5%数量
        "50-100亿 5%数量 比例": sz_gt50lt100_zd_gt5_ratio,  # 50-100亿 5%数量 比例
        "<50亿 5%数量": sz_lt50_zd_gt5,  # <50亿 5%数量
        "<50亿 5%数量 比例": sz_lt50_zd_gt5_ratio,  # <50亿 5%数量 比例
        ">10% 数量": zd_gt10,  # >10% 数量
        ">10% 数量 比例": zd_gt10_ratio,  # >10% 数量 比例
        ">5% 数量": zd_gt5,  # >5% 数量
        ">5% 数量 比例": zd_gt5_ratio,  # >5% 数量 比例
        ">3% 数量": zd_gt3,  # >3% 数量
        ">3% 数量 比例": zd_gt3_ratio  # >3% 数量 比例
    }


@router.get("/buy")
async def buy(zdcg: int):
    code_list = pgsql.get_db().query(WaitBuyList).all()
    list_ = [i.code for i in code_list]
    return list_[:zdcg]


@router.put(
    "/{item_id}",
    tags=["custom"],
    responses={403: {"description": "Operation forbidden"}},
)
async def update_item(item_id: str):
    if item_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the item: plumbus"
        )
    return {"item_id": item_id, "name": "The great Plumbus"}


def list_log_files(directory: str = os.getcwd()):
    files = []
    directory = os.path.join(directory, 'files')
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            files.append(filename)
    return files


@router.get("/files/")
async def get_files():
    files = list_log_files()
    return {"files": files}


@router.get("/download/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(os.getcwd(), "algo", "app", "files", filename)
    if os.path.isfile(filepath):
        return FileResponse(filepath, media_type='application/octet-stream', filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/excel/")
async def get_data_excel():
    # flag：盘口异动类型，默认输出全部类型的异动情况。
    # 可选：['火箭发射', '快速反弹','加速下跌', '高台跳水', '大笔买入', '大笔卖出', '封涨停板','封跌停板', '打开跌停板','打开涨停板','有大买盘','有大卖盘',
    # '竞价上涨', '竞价下跌','高开5日线','低开5日线', '向上缺口','向下缺口', '60日新高','60日新低','60日大幅上涨', '60日大幅下跌'] 上述异动类型分别可使用1-22数字代替。
    # 获取沪深A股最新行情指标
    # code_list = ['比亚迪', '上证指数']
    # df=qs.realtime_data(code=code_list)
    # # 获取个股试试交易快照
    # qs.stock_snapshot('比亚迪')

    # # 实时交易盘口异动数据
    # df=qs.realtime_change('60日新高')
    # #查看前几行
    # df.head()
    #     #异动类型：火箭发射
    # df=qs.realtime_change(1)
    # #查看前几行
    # df.head()

    # 沪深个股股东数量
    # stock_holder_num(date=None) 获取沪深A股市场公开的股东数目变化情况
    # date : 默认最新的报告期, 指定某季度如'2022-03-31','2022-06-30','2022-09-30','2022-12-31'
    # df=qs.stock_holder_num('20220930')
    # df
    # ------------------------------------------------------------------------
    # df=qs.intraday_data('比亚迪')       # 当日成交所有成交记录
    # ------------------------------------------------------------------------
    quotation = easyquotation.use('tencent')
    # loaded_codes_list=quotation.load_stock_codes()
    # loaded_codes_list
    all_market_dict = quotation.all_market
    print(all_market_dict)
    # data = {"日期":[],
    #         ">100亿10%数量":[],
    #         "(总数1354)占比%":[],
    #         ">50亿<100亿10%数量":[],
    #         "(总数1116)占比%":[],
    #         "<50亿10%数量":[],
    #         "(总数2883)占比%":[],
    #         ">100亿5%数量":[],
    #         "(总数1354)占比%":[],
    #         ">50且<100亿5%数量":[],
    #         "(总数1116)占比%":[],
    #         ">50亿5%数量":[],
    #         "(总数2883)占比%":[],
    #         "两市公司数量":[]}
    data = {"日期": [],
            "涨超10%": [],
            "涨超5%": [],
            "涨超3%": [],
            "5日涨超5%": [],
            "5日涨超10%": [],
            "跌超10%": [],
            "跌超5%": [],
            "跌超3%": [],
            "5日跌超5%": [],
            "5日跌超10%": [],
            "昨5%中继续上涨": [],
            "比例": [],
            "昨涨5%中继续5%": [],
            "占比": [],
            "站稳10日均线": [],
            "站稳20日均线": [],
            "站稳60日均线": [],
            "A股公司数量": [],
            "沪成交额": [],
            "深成交额": [],
            "创业板": [],
            "宗成交额": [],
            }
    df = pd.DataFrame(all_market_dict).T
    for key in all_market_dict.keys():
        print(key)
        print(all_market_dict[key])


@router.get("/tj")
async def get_tj(qm: str, info: str):
    pgsql.create(tjItem(qm=qm, info=info))
    return {"data": "添加成功", "code": 200}


@router.get("/ck")
async def get_ck(qm: str = None):
    if qm is not None:
        return pgsql.get_db().query(tjItem).filter(tjItem.qm == qm).all()
    return pgsql.read(tjItem)


@router.get("/sc")
async def get_ck(qm: str, info: str):
    for i in pgsql.get_db().query(tjItem).filter(and_(tjItem.qm == qm, tjItem.info.like(f'%{info}%'))).all():
        pgsql.get_db().delete(i)
    pgsql.get_db().commit()
    return {"data": "删除成功", "code": 200}


@router.get("/market_data")
def market_data():
    all_info = pd.DataFrame(quotation.market_snapshot(prefix=True).values())
    # >100亿 总量
    sz_gt100 = len(all_info[all_info['总市值'] >= 100])
    # >100亿 10%数量
    sz_gt100_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] >= 100)])
    # >100亿 3%-7%数量
    sz_gt100_zd_gt3lt7 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 100)])
    # >100亿 0%--3%数量
    sz_gt100_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 100)])
    # >100亿 -3%-0%%数量
    sz_gt100_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] >= 100)])
    # >100亿 -7%-3%数量
    sz_gt100_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 100)])
    # >100亿 -10%-7%数量
    sz_gt100_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) &(all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 100)])
    # >100亿 -10%%数量
    sz_gt100_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] >= 100)])
    # 50-100亿 总量
    sz_gt50lt100 = len(all_info[(all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
    # 50-100亿 10%数量
    sz_gt50lt100_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
    # 50-100亿 7%--3%数量
    sz_gt50lt100_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 0%--3%数量
    sz_gt50lt100_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -3%-0%%数量
    sz_gt50lt100_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -7%-3%数量
    sz_gt50lt100_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -10%-7%数量
    sz_gt50lt100_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) &(all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -10%%数量
    sz_gt50lt100_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] > 50) & (all_info['总市值'] < 100)])
    # <50亿 总量
    sz_lt50 = len(all_info[all_info['总市值'] < 50])
    # <50亿 10%数量
    sz_lt50_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] <= 50)])

    # <50亿 7%--3%数量
    sz_lt50_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] > 3) & (all_info['涨跌(%)'] < 7) & (all_info['总市值'] < 50)])
    # <50亿 0%--3%数量
    sz_lt50_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] > 0) & (all_info['涨跌(%)'] < 3) & (all_info['总市值'] < 50)])
    # <50亿 -3%-0%%数量
    sz_lt50_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] > -3) & (all_info['涨跌(%)'] < 0) & (all_info['总市值'] < 50)])
    # <50亿 -7%-3%数量
    sz_lt50_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] > -7) & (all_info['涨跌(%)'] < -3) & (all_info['总市值'] < 50)])
    # <50亿 -10%-7%数量
    sz_lt50_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] > -10) &(all_info['涨跌(%)'] < -7) & (all_info['总市值'] < 50)])
    # <50亿 -10%%数量
    sz_lt50_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] < 50)])

    # >100亿 5%数量
    sz_gt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] > 100)])
    # 50-100亿 5%数量
    sz_gt50lt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 100) & (all_info['总市值'] > 50)])
    # <50亿 5%数量
    sz_lt50_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 50)])
    # >10% 数量
    zd_gt10 = len(all_info[all_info['涨跌(%)'] > 10])
    # >5% 数量
    zd_gt5 = len(all_info[all_info['涨跌(%)'] > 5])
    # >3% 数量
    zd_gt3 = len(all_info[all_info['涨跌(%)'] > 3])


    # ---------------------盘后--------------------------------
    # 5日 涨超5%数量
    # res = wc.get(query='5日涨幅超过5%')
    # # 5日 涨超10%数量
    # res = wc.get(query='5日涨幅超过10%')
    # # 跌超 10%数量
    # zd_lt10 = all_info[all_info['涨跌(%)'] < -10]
    return {
        "sz_gt100": sz_gt100,
        "sz_gt100_zd_gt10": sz_gt100_zd_gt10,
        "sz_gt100_zd_gt3lt7": sz_gt100_zd_gt3lt7,
        "sz_gt100_zd_gt0lt3": sz_gt100_zd_gt0lt3,
        "sz_gt100_zd_gt_3lt0": sz_gt100_zd_gt_3lt0,
        "sz_gt100_zd_gt_7lt_3": sz_gt100_zd_gt_7lt_3,
        "sz_gt100_zd_gt_7lt_10": sz_gt100_zd_gt_7lt_10,
        "sz_gt100_zd_lt_10": sz_gt100_zd_lt_10,
        "sz_gt50lt100": sz_gt50lt100,
        "sz_gt50lt100_zd_gt10": sz_gt50lt100_zd_gt10,
        "sz_gt50lt100_zd_lt7gt3": sz_gt50lt100_zd_lt7gt3,
        "sz_gt50lt100_zd_gt0lt3": sz_gt50lt100_zd_gt0lt3,
        "sz_gt50lt100_zd_gt_3lt0": sz_gt50lt100_zd_gt_3lt0,
        "sz_gt50lt100_zd_gt_7lt_3": sz_gt50lt100_zd_gt_7lt_3,
        "sz_gt50lt100_zd_gt_7lt_10": sz_gt50lt100_zd_gt_7lt_10,
        "sz_gt50lt100_zd_lt_10": sz_gt50lt100_zd_lt_10,
        "sz_lt50": sz_lt50,
        "sz_lt50_zd_gt10": sz_lt50_zd_gt10,
        "sz_lt50_zd_lt7gt3": sz_lt50_zd_lt7gt3,
        "sz_lt50_zd_gt0lt3": sz_lt50_zd_gt0lt3,
        "sz_lt50_zd_gt_3lt0": sz_lt50_zd_gt_3lt0,
        "sz_lt50_zd_gt_7lt_3": sz_lt50_zd_gt_7lt_3,
        "sz_lt50_zd_gt_7lt_10": sz_lt50_zd_gt_7lt_10,
        "sz_lt50_zd_lt_10": sz_lt50_zd_lt_10,
        "sz_gt100_zd_gt5": sz_gt100_zd_gt5,
        "sz_gt50lt100_zd_gt5": sz_gt50lt100_zd_gt5,
        "sz_lt50_zd_gt5": sz_lt50_zd_gt5,
        "zd_gt10": zd_gt10,
        "zd_gt5": zd_gt5,
        "zd_gt3": zd_gt3
    }


@router.get("/tsgp")
async def tsgp():
    res = wc.get(query='9:20之前的竞价出现涨跌停价挂单加分,剔除ST')
    # BASE_URL = "http://0.0.0.0:8000"
    # files = list_log_files()
    # files.sort()
    # filename = files[-1]
    # file_url = f"{BASE_URL}/files/{filename}"
    # filepath = os.path.join(os.getcwd(), "files", filename)
    # if os.path.isfile(filepath):
    #     # return FileResponse(filepath, filename=file_url)
    #     return file_url
    # else:
    #     raise HTTPException(status_code=404, detail="File not found")
    print(res)
    return res.to_dict()
@router.get("/stock_list")
async def stock_list():
    BASE_URL = "http://0.0.0.0:8000"
    files = list_log_files()
    files.sort()
    filename = files[-1]
    file_url = f"{BASE_URL}/files/{filename}"
    filepath = os.path.join(os.getcwd(), "files", filename)
    if os.path.isfile(filepath):
        # return FileResponse(filepath, filename=file_url)
        return file_url
    else:
        raise HTTPException(status_code=404, detail="File not found")
