from __future__ import annotations
from amm import PoolState
from router import exec_col_to_copx
from risk_guard import quote_with_slippage

def fmt(n): return f"{n:,.6f}"

def seed():
    # Pool XRP<->COPX ~ 2,500 COPX/XRP; Pool COL<->XRP ~ 20 COL/XRP
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    pool_col_x  = PoolState(x_reserve=10_000.0, y_reserve=200_000.0,   fee_bps=30)
    return pool_col_x, pool_x_copx

def main():
    poolA, poolB = seed()

    col_in   = 8_000.0
    slip_bps = 150  # 1.50% tolerance

    # Non-mutating guarded quote
    gq = quote_with_slippage(poolA, poolB, col_in, slip_bps)
    print(f"Quote: {fmt(col_in)} COL → {fmt(gq.copx_out_quote)} COPX | min_out @{slip_bps} bps = {fmt(gq.min_out)}")

    # Execute against fresh copies (simulate a real fill that follows the quote)
    poolA2, poolB2 = seed()
    r_exec = exec_col_to_copx(poolA2, poolB2, col_in)  # RouteResult
    copx_out = r_exec.amount_out
    ok = copx_out >= gq.min_out
    print(f"Exec:  {fmt(col_in)} COL → {fmt(copx_out)} COPX | {'OK' if ok else 'SLIPPED TOO FAR!'}")

if __name__ == "__main__":
    main()

