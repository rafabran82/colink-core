#!/usr/bin/env python3
"""
XRPL Testnet Bootstrap — Module 1
Phase: Imports + Constants
"""

import sys
import json
import time
import logging
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet

# === Constants ===
JSON_RPC_TESTNET = "https://s.altnet.rippletest.net:51234"
CURRENCY_CODE = "COPX"
