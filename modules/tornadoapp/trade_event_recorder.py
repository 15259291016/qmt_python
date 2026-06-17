from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional

import logging

logger = logging.getLogger(__name__)

_LOCAL_LOCK = None  # 延迟创建，避免导入期开销


def _get_local_lock():
    """进程内锁：防止同一进程多线程并发写同一个 Excel 文件导致损坏。"""
    global _LOCAL_LOCK
    if _LOCAL_LOCK is None:
        import threading

        _LOCAL_LOCK = threading.Lock()
    return _LOCAL_LOCK


def _normalize_row(
    event_type: str,
    symbol: str,
    *,
    reason: str,
    stock_name: Optional[str] = None,
    side: Optional[str] = None,
    pnl_pct: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    now = datetime.now()
    row: Dict[str, Any] = {
        "日期": now.strftime("%Y-%m-%d"),
        "时间": now.strftime("%H:%M:%S"),
        "事件类型": event_type,
        "股票代码": symbol,
        "股票名称": stock_name or "",
        "买卖方向": side or "",
        "原因": reason,
    }

    if pnl_pct is not None:
        try:
            row["盈亏百分比"] = float(pnl_pct)
        except (TypeError, ValueError):
            row["盈亏百分比"] = pnl_pct

    if extra:
        for k, v in extra.items():
            row[str(k)] = v
    return row


def _spool_pending(file_path: Path, row: Dict[str, Any]) -> None:
    """当 Excel 被占用/写入失败时，将事件追加到本地待写队列，避免丢失。"""
    pending_path = file_path.with_suffix(file_path.suffix + ".pending.jsonl")
    try:
        pending_path.parent.mkdir(parents=True, exist_ok=True)
        with pending_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        # 兜底：连待写队列也写不了就算了，不要影响交易
        logger.error("写入待写队列失败: %s", pending_path, exc_info=True)


def _load_pending(file_path: Path, max_lines: int = 2000) -> list[Dict[str, Any]]:
    """读取待写队列（最多 max_lines 行），用于在下次成功写入时补齐。"""
    pending_path = file_path.with_suffix(file_path.suffix + ".pending.jsonl")
    if not pending_path.exists():
        return []
    rows: list[Dict[str, Any]] = []
    try:
        with pending_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        logger.error("读取待写队列失败: %s", pending_path, exc_info=True)
        return []
    return rows


def _truncate_pending(file_path: Path, consumed: int) -> None:
    """成功写入后，从待写队列中移除已消费的行。"""
    if consumed <= 0:
        return
    pending_path = file_path.with_suffix(file_path.suffix + ".pending.jsonl")
    if not pending_path.exists():
        return
    try:
        with pending_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        remaining = lines[consumed:]
        if remaining:
            with pending_path.open("w", encoding="utf-8") as f:
                f.writelines(remaining)
        else:
            pending_path.unlink(missing_ok=True)
    except Exception:
        logger.error("清理待写队列失败: %s", pending_path, exc_info=True)


def _append_rows_to_excel(file_path: Path, rows: list[Dict[str, Any]]) -> None:
    """
    使用 openpyxl 逐行追加写入同一个 Excel。
    - 不读取整表，避免性能问题
    - 若遇到文件被占用/权限问题，抛出异常交由上层兜底
    """
    # 延迟导入：避免没有安装 openpyxl 时影响主流程（仍会被上层捕获）
    from openpyxl import Workbook, load_workbook  # type: ignore[import]

    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        wb = load_workbook(file_path)
        ws = wb.active
        # 获取已存在表头
        header_cells = list(ws[1]) if ws.max_row >= 1 else []
        headers = [c.value for c in header_cells if c.value is not None]
    else:
        wb = Workbook()
        ws = wb.active
        headers = []

    # 统一表头：包含所有出现过的 key（先保留已有顺序，再追加新字段）
    key_order: list[str] = headers[:]
    seen = set(key_order)
    for r in rows:
        for k in r.keys():
            if k not in seen:
                key_order.append(k)
                seen.add(k)

    # 若表头为空/需要扩展，写入/补齐表头
    if not headers:
        ws.append(key_order)
    elif key_order != headers:
        # 补齐表头：只在末尾追加新列，保持已存在列不变
        for k in key_order[len(headers) :]:
            ws.cell(row=1, column=len(headers) + 1, value=k)
            headers.append(k)

    # 追加数据行
    for r in rows:
        ws.append([r.get(k, "") for k in key_order])

    wb.save(file_path)


def record_trade_event(
    event_type: str,
    symbol: str,
    *,
    reason: str,
    stock_name: Optional[str] = None,
    side: Optional[str] = None,
    pnl_pct: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
    file_path: Path | str = "logs/trade_events.xlsx",
) -> None:
    """将关键交易事件记录到 Excel，便于事后复盘。

    设计目标：
    - 把「无法买入」「无法卖出」「已触发卖出并下单」等事件，统一记到一个表里
    - 字段包含：日期、时间、事件类型、股票代码/名称、买卖方向、原因、盈亏百分比、额外信息
    - 不中断实盘：即使写 Excel 失败，也只记录日志，不影响交易主流程
    """
    try:
        file_path = Path(file_path)
        row = _normalize_row(
            event_type,
            symbol,
            reason=reason,
            stock_name=stock_name,
            side=side,
            pnl_pct=pnl_pct,
            extra=extra,
        )

        # 先把 pending 一起补写（如果存在），再写入当前这一条，保证最终只有一个 Excel
        lock = _get_local_lock()
        with lock:
            pending_rows = _load_pending(file_path)
            rows_to_write = pending_rows + [row]
            try:
                _append_rows_to_excel(file_path, rows_to_write)
                # 成功后清理已消费 pending（全部消费）
                if pending_rows:
                    _truncate_pending(file_path, consumed=len(pending_rows))
            except PermissionError as e:
                # 常见原因：Excel 正在打开文件，Windows 会锁定，无法写入
                logger.warning("Excel 文件被占用，先写入待写队列，稍后自动补写: %s (%s)", file_path, e)
                _spool_pending(file_path, row)
            except Exception as e:
                # 其它异常：同样写入待写队列，避免丢事件
                logger.error("写入 Excel 失败，先写入待写队列，稍后自动补写: %s (%s)", file_path, e, exc_info=True)
                _spool_pending(file_path, row)
    except Exception as e:
        # 任何异常都只记录日志，不影响主流程
        logger.error("记录交易事件到 Excel 失败: %s", e, exc_info=True)


