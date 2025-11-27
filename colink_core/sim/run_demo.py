from amm import PoolState
from wallet import Wallet


def fmt(n):
    return f"{n:,.6f}"


def main():
    # 1) Seed pool so initial price ~ 2,500 COPX per 1 XRP (example)
    pool = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    maker = Wallet(x=10_000.0, y=25_000_000.0)
    trader = Wallet(x=1_000.0, y=5_000_000.0)

    print("== Seed Liquidity ==")
    print("Initial price (COPX per XRP):", fmt(pool.price_y_per_x()))
    # add a little more liquidity to demonstrate add/remove
    minted = pool.add_liquidity(dx=1_000.0, dy=2_500_000.0)
    maker.debit_x(1_000.0)
    maker.debit_y(2_500_000.0)
    print("Added liquidity; LP units ~", fmt(minted))
    print("Reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print()

    # 2) Swap scenario: buy COPX with XRP
    print("== Swap: XRP â†’ COPX ==")
    dx = 100.0
    trader.debit_x(dx)
    dy_out, px = pool.swap_x_for_y(dx)
    trader.credit_y(dy_out)
    print(f"Swapped {fmt(dx)} XRP for {fmt(dy_out)} COPX at effective {fmt(px)} COPX/XRP")
    print("New price (COPX per XRP):", fmt(pool.price_y_per_x()))
    print("Reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print()

    # 3) Swap other side: buy XRP with COPX
    print("== Swap: COPX â†’ XRP ==")
    dy_in = 250_000.0
    trader.debit_y(dy_in)
    dx_out, px_xy = pool.swap_y_for_x(dy_in)
    trader.credit_x(dx_out)
    print(f"Swapped {fmt(dy_in)} COPX for {fmt(dx_out)} XRP at effective {fmt(px_xy)} XRP/COPX")
    print("New price (COPX per XRP):", fmt(pool.price_y_per_x()))
    print("Reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print()

    # 4) Remove 10% liquidity
    print("== Remove Liquidity 10% ==")
    dx_w, dy_w = pool.remove_liquidity(0.10)
    maker.credit_x(dx_w)
    maker.credit_y(dy_w)
    print("Withdrew: X=", fmt(dx_w), " Y=", fmt(dy_w))
    print("Reserves: X=", fmt(pool.x_reserve), " Y=", fmt(pool.y_reserve))
    print("Price (COPX per XRP):", fmt(pool.price_y_per_x()))


if __name__ == "__main__":
    main()

