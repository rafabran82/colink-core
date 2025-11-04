from __future__ import annotations
from amm import PoolState
from router import exec_col_to_copx
from risk_guard import quote_with_slippage

def fmt(n): return f"{n:,.6f}"

def seed():
    # Same seeds as before
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)  # XRP<->COPX
    pool_col_x  = PoolState(x_reserve=10_000.0, y_reserve=200_000.0,   fee_bps=30)  # XRP<->COL
    return pool_col_x, pool_x_copx

def main():
    # Step 1: quote on clean pools
    poolA, poolB = seed()
    col_in   = 8_000.0
    slip_bps = 150  # 1.50% tolerance

    gq = quote_with_slippage(poolA, poolB, col_in, slip_bps)
    print(f"Quote: {fmt(col_in)} COL → {fmt(gq.copx_out_quote)} COPX | min_out @{slip_bps} bps = {fmt(gq.min_out)}")

    # Step 2: new copies for execution... but someone moves the market against us
    poolA2, poolB2 = seed()

    # Adverse move #1 on XRP<->COPX: add XRP, pull COPX (reduces COPX per XRP => worse for our x->y hop)
    # Large enough to push price down materially
    pulled_copx, _effB = poolB2.swap_x_for_y(5_000.0)  # add 5k XRP, withdraw COPX

    # Adverse move #2 on COL<->XRP (optional but makes failure certain): add COL, pull XRP (reduces our hop1 XRP out)
    _xrp_out_front, _effA = poolA2.swap_y_for_x(50_000.0)  # drain XRP liquidity

    # Step 3: try to execute after the adverse moves
    r_exec = exec_col_to_copx(poolA2, poolB2, col_in)
    copx_out = r_exec.amount_out
    ok = copx_out >= gq.min_out
    print(f"Exec:  {fmt(col_in)} COL → {fmt(copx_out)} COPX | {'OK' if ok else 'SLIPPED TOO FAR!'}")

    # Helpful context
    print("Note: guard should stop the trade if enforced on-chain.")

if __name__ == "__main__":
    main()

