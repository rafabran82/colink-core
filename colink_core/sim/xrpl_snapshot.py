from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


# -----------------------------
# Data models
# -----------------------------


@dataclass
class AccountIOU:
    currency: str
    balance: float
    limit: float


@dataclass
class AccountSnapshot:
    address: str
    xrp: Optional[float] = None
    ious: List[AccountIOU] = None


@dataclass
class BalancesSnapshot:
    issuer: AccountSnapshot
    user: AccountSnapshot
    lp: AccountSnapshot


@dataclass
class OrderbookOffer:
    account: str
    taker_gets_currency: str
    taker_gets_value: float
    taker_pays_currency: str
    taker_pays_value: float
    quality: Optional[float]


@dataclass
class OrderbookSnapshot:
    ledger_index: Optional[int]
    offers: List[OrderbookOffer]


@dataclass
class BridgeStateSnapshot:
    network: str
    issuer: str
    user: str
    lp: str
    copx_hex: str
    col_code: str
    orderbook_offers: int
    bridge_status: str
    bridge_tx_hash: Optional[str]


@dataclass
class BootstrapSnapshot:
    base_dir: Path
    balances: Optional[BalancesSnapshot]
    orderbook: Optional[OrderbookSnapshot]
    bridge_state: Optional[BridgeStateSnapshot]


# -----------------------------
# Helpers
# -----------------------------


def _safe_load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_account_snapshot(raw: Dict[str, Any]) -> AccountSnapshot:
    addr = raw.get("address", "")
    xrp_raw = raw.get("xrp")
    try:
        xrp_val = float(xrp_raw) if xrp_raw is not None else None
    except Exception:
        xrp_val = None

    ious_list = []
    for iou in raw.get("ious", []) or []:
        try:
            ious_list.append(
                AccountIOU(
                    currency=str(iou.get("currency", "")),
                    balance=float(iou.get("balance", 0)),
                    limit=float(iou.get("limit", 0)),
                )
            )
        except Exception:
            # Be forgiving on bad entries
            continue

    return AccountSnapshot(address=addr, xrp=xrp_val, ious=ious_list)


def _load_balances(path: Path) -> Optional[BalancesSnapshot]:
    raw = _safe_load_json(path)
    if not isinstance(raw, dict):
        return None

    issuer = _parse_account_snapshot(raw.get("issuer", {}) or {})
    user = _parse_account_snapshot(raw.get("user", {}) or {})
    lp = _parse_account_snapshot(raw.get("lp", {}) or {})

    return BalancesSnapshot(issuer=issuer, user=user, lp=lp)


def _load_orderbook(path: Path) -> Optional[OrderbookSnapshot]:
    raw = _safe_load_json(path)
    if not isinstance(raw, dict):
        return None

    ledger_idx = raw.get("ledger_current_index")
    try:
        ledger_idx = int(ledger_idx) if ledger_idx is not None else None
    except Exception:
        ledger_idx = None

    offers_out: List[OrderbookOffer] = []
    for off in raw.get("offers", []) or []:
        try:
            account = str(off.get("Account", ""))

            gets = off.get("TakerGets", {}) or {}
            pays = off.get("TakerPays", {}) or {}

            gets_curr = str(gets.get("currency", ""))
            pays_curr = str(pays.get("currency", ""))

            gets_val_raw = gets.get("value")
            pays_val_raw = pays.get("value")

            gets_val = float(gets_val_raw) if gets_val_raw is not None else 0.0
            pays_val = float(pays_val_raw) if pays_val_raw is not None else 0.0

            q_raw = off.get("quality")
            try:
                q_val = float(q_raw) if q_raw is not None else None
            except Exception:
                q_val = None

            offers_out.append(
                OrderbookOffer(
                    account=account,
                    taker_gets_currency=gets_curr,
                    taker_gets_value=gets_val,
                    taker_pays_currency=pays_curr,
                    taker_pays_value=pays_val,
                    quality=q_val,
                )
            )
        except Exception:
            continue

    return OrderbookSnapshot(ledger_index=ledger_idx, offers=offers_out)


def _load_bridge_state(path: Path) -> Optional[BridgeStateSnapshot]:
    raw = _safe_load_json(path)
    if not isinstance(raw, dict):
        return None

    return BridgeStateSnapshot(
        network=str(raw.get("network", "")),
        issuer=str(raw.get("issuer", "")),
        user=str(raw.get("user", "")),
        lp=str(raw.get("lp", "")),
        copx_hex=str(raw.get("copx_hex", "")),
        col_code=str(raw.get("col_code", "")),
        orderbook_offers=int(raw.get("orderbook_offers", 0) or 0),
        bridge_status=str(raw.get("bridge_status", "")),
        bridge_tx_hash=raw.get("bridge_tx_hash"),
    )


def load_bootstrap_snapshot(base_dir: str | Path = ".artifacts/data/bootstrap") -> BootstrapSnapshot:
    """
    Load XRPL bootstrap artifacts (balances, orderbook, bridge_state) into
    a structured snapshot object for use by the simulator.

    This is intentionally forgiving: if a file is missing or malformed,
    the corresponding field will be None.
    """
    base = Path(base_dir)
    balances_path = base / "balances_copx_col.json"
    orderbook_path = base / "orderbook_copx_col.json"
    bridge_state_path = base / "bridge_state.json"

    balances = _load_balances(balances_path)
    orderbook = _load_orderbook(orderbook_path)
    bridge_state = _load_bridge_state(bridge_state_path)

    return BootstrapSnapshot(
        base_dir=base,
        balances=balances,
        orderbook=orderbook,
        bridge_state=bridge_state,
    )


# -----------------------------
# Small CLI for debugging
# -----------------------------


def _format_account_line(label: str, acct: AccountSnapshot) -> str:
    parts = [f"{label}: {acct.address}"]
    if acct.xrp is not None:
        parts.append(f"  XRP={acct.xrp:.6f}")
    if acct.ious:
        ious_desc = ", ".join(
            f"{iou.currency}: {iou.balance} / {iou.limit}" for iou in acct.ious
        )
        parts.append(f"  IOUs=[{ious_desc}]")
    return " | ".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect XRPL bootstrap snapshot (balances, orderbook, bridge_state)."
    )
    parser.add_argument(
        "--base-dir",
        default=".artifacts/data/bootstrap",
        help="Directory containing balances_copx_col.json, orderbook_copx_col.json, bridge_state.json",
    )
    args = parser.parse_args(argv)

    snap = load_bootstrap_snapshot(args.base_dir)

    print(f"XRPL Bootstrap Snapshot @ {snap.base_dir}")
    print("-" * 60)

    if snap.bridge_state:
        bs = snap.bridge_state
        print(f"Network: {bs.network}")
        print(f"Issuer:  {bs.issuer}")
        print(f"User:    {bs.user}")
        print(f"LP:      {bs.lp}")
        print(f"COPX_HEX: {bs.copx_hex}  |  COL_CODE: {bs.col_code}")
        print(f"Orderbook offers (bridge_state): {bs.orderbook_offers}")
        print(f"Bridge status: {bs.bridge_status}")
        print(f"Bridge tx hash: {bs.bridge_tx_hash}")
        print()

    if snap.balances:
        print("Balances:")
        print("  " + _format_account_line("Issuer", snap.balances.issuer))
        print("  " + _format_account_line("User", snap.balances.user))
        print("  " + _format_account_line("LP", snap.balances.lp))
        print()

    if snap.orderbook:
        ob = snap.orderbook
        print(f"Orderbook ledger index: {ob.ledger_index}")
        print(f"Order count: {len(ob.offers)}")
        if ob.offers:
            best = sorted(
                [o for o in ob.offers if o.quality is not None],
                key=lambda o: o.quality,
            )
            if best:
                b = best[0]
                print(
                    "Best offer: "
                    f"{b.taker_gets_value} {b.taker_gets_currency} -> "
                    f"{b.taker_pays_value} {b.taker_pays_currency} "
                    f"(quality={b.quality})"
                )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
