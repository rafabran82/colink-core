import re, sys, pathlib

path = pathlib.Path("scripts/xrpl.testnet.bootstrap.py")
src  = path.read_text(encoding="utf-8")

# 1) Ensure the IssuedCurrencyAmount import exists (right after TrustSet import if possible)
if "from xrpl.models.amounts import IssuedCurrencyAmount" not in src:
    src = re.sub(
        r'^(from\s+xrpl\.models\.transactions\s+import\s+TrustSet\s*)$',
        r'\\1\nfrom xrpl.models.amounts import IssuedCurrencyAmount',
        src,
        flags=re.M
    )

# 2) Replace the whole trustline_tx() block
new_fn = r"""
def trustline_tx(issuer_addr: str, currency: str, limit: str):
    """
    Build a TrustSet with an IssuedCurrencyAmount (no Currency.from_currency_code).
    `currency` should be a standard code like "COL" (3-20 chars).
    """
    return TrustSet(
        limit_amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer_addr,
            value=limit
        )
    )
""".lstrip("\n")

pattern = re.compile(
    r"def\s+trustline_tx\([^)]*\):.*?(?=\ndef\s+|\nif\s+__name__\s*==\s*['\"]__main__['\"]\s*:|\Z)",
    flags=re.S | re.M,
)
if pattern.search(src):
    src = pattern.sub(new_fn, src)
else:
    print("WARN: trustline_tx() not found — no replacement made.", file=sys.stderr)

# 3) Remove any leftover Currency.from_currency_code(...) calls (belt & suspenders)
src = re.sub(r"Currency\.from_currency_code\s*\(\s*([^)]+?)\s*\)", r"\\1", src)

path.write_text(src, encoding="utf-8")
print("OK: patched trustline_tx and imports.")
