from dataclasses import dataclass


@dataclass
class SwapResult:
    amount_out: float
    fee_charged: float
    price: float
    slippage: float


class SwapCalculator:
    """
    Constant-product AMM swap engine with fee-on-input.
    """

    def compute_swap(
        self,
        reserve_in: float,
        reserve_out: float,
        amount_in: float,
        fee_rate: float,
    ) -> SwapResult:
        if amount_in <= 0:
            raise ValueError("amount_in must be positive")
        if reserve_in <= 0 or reserve_out <= 0:
            raise ValueError("reserves must be positive")

        pre_price = reserve_out / reserve_in

        amount_in_with_fee = amount_in * (1.0 - fee_rate)
        fee_charged = amount_in - amount_in_with_fee

        k = reserve_in * reserve_out
        new_reserve_in = reserve_in + amount_in_with_fee
        new_reserve_out = k / new_reserve_in
        amount_out = reserve_out - new_reserve_out

        if amount_out <= 0:
            raise ValueError("swap would produce non-positive output")

        effective_price = amount_out / amount_in

        if pre_price != 0:
            slippage = (pre_price - effective_price) / pre_price
        else:
            slippage = 0.0

        return SwapResult(
            amount_out=amount_out,
            fee_charged=fee_charged,
            price=effective_price,
            slippage=slippage,
        )
