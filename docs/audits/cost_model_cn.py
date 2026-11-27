# cost_model_cn.py —— A 股 ETF＋股票成本函数参考实现（外审交付·可直接对标替换）
# v1.0 · 2026-09-30 · 依据 docs/audits/instrument-rules-registry-20260930.md
#
# 为什么有这件：knowledge/rules.py 的 FeeSchedule 是 ETF 专用（stamp_tax=0.0 / transfer_fee=0.0），
# 且 total_buy_cost / total_sell_proceeds / cost_v2_side_rate 全部只用默认值——跑股票会漏税。
# 本件给出**按品种路由**的参考实现，逐项可对账、可单测。司内可直接对标替换（票号自领）。
#
# 与 rules.py 的关系：不是替代框架，是**补它的品种维度**。判据层仍以 BACKTEST_SCIENCE.md 为准。
"""A-share instrument cost model (ETF + stock). Futures intentionally absent (CEO 2026-09-30)."""

from dataclasses import dataclass

# ---------------------------------------------------------------- board routing
MAIN_BOARD_LIMIT = 0.10
CHINEXT_STAR_LIMIT = 0.20
BSE_LIMIT = 0.30
ST_LIMIT = 0.05
NEW_LISTING_FREE_SESSIONS = 5   # 上市首 5 个交易日无涨跌停


def board_of(code: str) -> str:
    """Route a 6-digit A-share code to its board. ETF families first (they overlap no stock prefix)."""
    c = str(code)
    if c.startswith(("60", "00")):
        return "main"
    if c.startswith("30"):
        return "chinext"
    if c.startswith("688"):
        return "star"
    if c.startswith(("8", "43")):
        return "bse"
    if c.startswith("5") or c.startswith("159"):
        return "etf"
    return "unknown"


def price_limit(code: str, is_st: bool = False, sessions_since_listing: int | None = None) -> float:
    """Daily band for the instrument. Returns float('inf') for the no-band window."""
    if sessions_since_listing is not None and sessions_since_listing < NEW_LISTING_FREE_SESSIONS:
        return float("inf")                      # 新股首 5 日无涨跌停
    b = board_of(code)
    if b == "etf":
        return MAIN_BOARD_LIMIT                  # ETF 一律 ±10%
    if is_st:
        return ST_LIMIT                          # ST ±5%
    if b in ("chinext", "star"):
        return CHINEXT_STAR_LIMIT
    if b == "bse":
        return BSE_LIMIT
    return MAIN_BOARD_LIMIT


def lot_size(code: str) -> int:
    """Minimum buy unit. STAR market buys from 200 shares (then 1-share increments)."""
    if board_of(code) == "star":
        return 200
    return 100


def is_t0(code: str) -> bool:
    """Same-day sell allowed. All stocks are T+1; only specific ETF families are T+0."""
    return str(code) in {
        "511260", "511090", "511010",            # 债券 ETF
        "518880", "159934",                      # 黄金 ETF
        "513100", "513500", "513050", "513180",  # 跨境 ETF
        "159920", "513520",
        "511880", "511990",                      # 货币 ETF
    }


# ---------------------------------------------------------------- fees
@dataclass(frozen=True)
class CnFees:
    """Exchange + regulatory + tax rates. Defaults are the current statutory levels."""
    commission_rate: float = 0.00025      # 万2.5, both sides, per broker agreement
    commission_min: float = 5.0           # CNY per order, BOTH sides
    handling_fee: float = 0.0000341       # 经手费, both sides
    supervision_fee: float = 0.00002      # 证管费, both sides
    transfer_fee_stock: float = 0.00001   # 过户费 0.001%, stocks only, BOTH sides
    stamp_tax_stock_sell: float = 0.0005  # 印花税 0.05%, stocks only, SELL ONLY
    slippage_tier_2bp: float = 0.0002
    slippage_tier_5bp: float = 0.0005
    slippage_tier_10bp: float = 0.001


ADV20_TIER_2BP_YUAN = 500_000_000.0       # >=5e8 -> 2bp
ADV20_TIER_5BP_YUAN = 100_000_000.0       # [1e8,5e8) -> 5bp; below -> 10bp
ADV_FILL_CAP_RATE = 0.01                  # demand above 1% of ADV does not fill


def is_etf(code: str) -> bool:
    return board_of(code) == "etf"


def slippage_rate(adv20_yuan, fees: CnFees = CnFees()) -> float:
    """ADV(20d)-tiered slippage. Missing/invalid input falls back to the 10bp tier:
    a data gap must never make costs cheaper."""
    try:
        v = float(adv20_yuan)
    except (TypeError, ValueError):
        return fees.slippage_tier_10bp
    if v != v:                                    # NaN
        return fees.slippage_tier_10bp
    if v >= ADV20_TIER_2BP_YUAN:
        return fees.slippage_tier_2bp
    if v >= ADV20_TIER_5BP_YUAN:
        return fees.slippage_tier_5bp
    return fees.slippage_tier_10bp


def _fixed_side_rate(code: str, fees: CnFees) -> float:
    """Non-slippage per-side rate. The ONLY place instrument type changes the maths."""
    r = fees.handling_fee + fees.supervision_fee
    if not is_etf(code):
        r += fees.transfer_fee_stock               # stocks pay transfer fee both sides
    return r


def buy_cost(price: float, qty: int, code: str, adv20_yuan=None,
             fees: CnFees = CnFees()) -> float:
    """Total cash out to buy qty. Stamp duty is deliberately absent (seller pays it)."""
    gross = price * qty
    commission = max(gross * fees.commission_rate, fees.commission_min)
    fixed = gross * _fixed_side_rate(code, fees)
    slip = gross * slippage_rate(adv20_yuan, fees)
    return gross + commission + fixed + slip


def sell_proceeds(price: float, qty: int, code: str, adv20_yuan=None,
                  fees: CnFees = CnFees()) -> float:
    """Net cash in from selling qty. Stamp duty applies to stocks only, sell side only."""
    gross = price * qty
    commission = max(gross * fees.commission_rate, fees.commission_min)
    fixed = gross * _fixed_side_rate(code, fees)
    slip = gross * slippage_rate(adv20_yuan, fees)
    stamp = 0.0 if is_etf(code) else gross * fees.stamp_tax_stock_sell
    return gross - commission - fixed - slip - stamp


def round_trip_cost_bp(code: str, price: float, qty: int, adv20_yuan=None,
                       fees: CnFees = CnFees()) -> float:
    """Effective round-trip cost in basis points of notional. The single number a
    preregistration should quote so ETF and stock results stay comparable."""
    gross = price * qty
    if gross <= 0:
        return 0.0
    spent = buy_cost(price, qty, code, adv20_yuan, fees) - gross
    got = gross - sell_proceeds(price, qty, code, adv20_yuan, fees)
    return (spent + got) / gross * 10000.0


def effective_commission_bp(notional: float, fees: CnFees = CnFees()) -> float:
    """Per-side commission in bp INCLUDING the CNY 5 floor. Below CNY 20,000 the floor bites."""
    if notional <= 0:
        return 0.0
    rate = max(notional * fees.commission_rate, fees.commission_min) / notional
    return rate * 10000.0


# ---------------------------------------------------------------- self-test
def _selftest() -> bool:
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        if not cond:
            ok = False
            print(f"FAIL {name} {detail}")

    # board routing
    chk("board main", board_of("600519") == "main" and board_of("000001") == "main")
    chk("board growth", board_of("300750") == "chinext" and board_of("688981") == "star")
    chk("board bse", board_of("830799") == "bse" and board_of("430047") == "bse")
    chk("board etf", board_of("510300") == "etf" and board_of("159915") == "etf")

    # bands
    chk("limit main", price_limit("600519") == 0.10)
    chk("limit growth", price_limit("300750") == 0.20 and price_limit("688981") == 0.20)
    chk("limit st", price_limit("600519", is_st=True) == 0.05)
    chk("limit new listing", price_limit("600519", sessions_since_listing=2) == float("inf"))
    chk("limit after 5 sessions", price_limit("600519", sessions_since_listing=5) == 0.10)

    # lots and T+0
    chk("lot star", lot_size("688981") == 200 and lot_size("600519") == 100)
    chk("t0 cross-border", is_t0("513100") and not is_t0("510300"))

    # stamp duty: absent on buy, present on sell, absent for ETF
    f = CnFees()
    px, q = 10.0, 10000          # 100,000 CNY notional
    stock = "600519"
    etf = "510300"
    thr = 0.0001                 # tolerance in CNY
    # identical inputs except instrument -> the difference must be exactly the stock extras
    buy_stock = buy_cost(px, q, stock, None, f)
    buy_etf = buy_cost(px, q, etf, None, f)
    sell_stock = sell_proceeds(px, q, stock, None, f)
    sell_etf = sell_proceeds(px, q, etf, None, f)
    gross = px * q
    # buy: stock pays transfer fee only (no stamp duty)
    chk("buy transfer only", abs((buy_stock - buy_etf) - gross * f.transfer_fee_stock) < thr)
    # sell: stock pays transfer fee AND stamp duty
    chk("sell transfer+stamp",
        abs((sell_etf - sell_stock) - gross * (f.transfer_fee_stock + f.stamp_tax_stock_sell)) < thr)

    # minimum commission bites below 20k
    chk("commission floor 5k", abs(effective_commission_bp(5000.0, f) - 10.0) < 0.01)
    chk("commission normal 100k", abs(effective_commission_bp(100000.0, f) - 2.5) < 0.01)

    # round-trip comparability: stock must exceed ETF by roughly stamp+transfer
    rt_etf = round_trip_cost_bp(etf, px, q, None, f)
    rt_stock = round_trip_cost_bp(stock, px, q, None, f)
    chk("round trip stock > etf", rt_stock > rt_etf, f"{rt_stock} vs {rt_etf}")

    print(f"selftest {'PASS' if ok else 'FAIL'}   etf_rt={rt_etf:.2f}bp  stock_rt={rt_stock:.2f}bp  "
          f"delta={rt_stock - rt_etf:.2f}bp")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if _selftest() else 1)
