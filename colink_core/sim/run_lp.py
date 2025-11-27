from __future__ import annotations

from amm import PoolState


def fmt(n):
    return f"{n:,.6f}"


def seed(protocol_fee_bps=5):
    # Start similar to your earlier pool (1 XRP ~ 2,500 COPX)
    pool = PoolState(
        x_reserve=10_000.0,
        y_reserve=25_000_000.0,
        fee_bps=30,  # 0.30% total fee
        protocol_fee_bps=protocol_fee_bps,  # e.g., 0.05% out of the 0.30% goes to protocol
    )
    # Mint initial LP: add_liquidity uses sqrt(dx*dy) on first deposit
    pool.add_liquidity(1_000.0, 2_500_000.0)
    return pool


def main():
    pool = seed()
    print("== Seed ==")
    print("Reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print("LP total:", fmt(pool.lp_total))
    print("Price (COPX per XRP):", fmt(pool.price_y_per_x))
    print()

    # Simulated flow of trades
    swaps = [
        ("x_for_y", 100.0),
        ("y_for_x", 250_000.0),
        ("x_for_y", 500.0),
        ("y_for_x", 1_000_000.0),
    ]
    for side, amt in swaps:
        if side == "x_for_y":
            out, px = pool.swap_x_for_y(amt)
            print(f"Swap Xâ†’Y: in {fmt(amt)} XRP, out {fmt(out)} COPX, eff {fmt(px)} COPX/XRP")
        else:
            out, px = pool.swap_y_for_x(amt)
            print(f"Swap Yâ†’X: in {fmt(amt)} COPX, out {fmt(out)} XRP, eff {fmt(px)} XRP/COPX")

    print("\n== Post-swaps ==")
    print("Reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print("LP fees tallies: X=", fmt(pool.lp_fees_x), " Y=", fmt(pool.lp_fees_y))
    print(
        "Protocol fees tallies (off-pool): X=",
        fmt(pool.proto_fees_x),
        " Y=",
        fmt(pool.proto_fees_y),
    )
    print("LP total:", fmt(pool.lp_total))
    print("Price (COPX per XRP):", fmt(pool.price_y_per_x))

    # LP withdraws 10%
    dx, dy = pool.remove_liquidity(0.10)
    print("\n== LP withdraw 10% ==")
    print("Withdrawn: X=", fmt(dx), " Y=", fmt(dy))
    print("New reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print("LP total:", fmt(pool.lp_total))


if __name__ == "__main__":
    main()

