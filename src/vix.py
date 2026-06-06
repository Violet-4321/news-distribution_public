from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf


@dataclass(frozen=True)
class VixSnapshot:
    value: float | None
    interpretation: str


def get_vix_snapshot() -> VixSnapshot:
    try:
        history = yf.Ticker("^VIX").history(period="5d", interval="1d")
    except Exception:
        return VixSnapshot(value=None, interpretation="VIX 获取失败，无法判断当前市场波动情绪。")

    if history.empty:
        return VixSnapshot(value=None, interpretation="VIX 暂无可用数据，无法判断当前市场波动情绪。")

    value = float(history["Close"].dropna().iloc[-1])
    return VixSnapshot(value=value, interpretation=_interpret_vix(value))


def _interpret_vix(value: float) -> str:
    if value < 15:
        return "市场波动预期偏低，投资者情绪相对平稳。"
    if value < 20:
        return "市场波动预期处于正常区间，风险偏好整体中性。"
    if value < 30:
        return "市场波动预期升高，投资者对风险事件更敏感。"
    return "市场波动预期处于高位，市场避险情绪明显。"
