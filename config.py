"""
config.py

Central configuration for the MEV arbitrage bot demo.

IMPORTANT: This is a portfolio/demo project. It does NOT sign or broadcast
any transactions (see executor.py). Do not paste a real private key into
this file, a .env file, or anywhere else in this repo. Use environment
variables and a burner wallet if you ever extend this into something that
touches mainnet.
"""

import os

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

# Any standard JSON-RPC HTTPS endpoint works here (Infura, Alchemy, a local
# node, etc). Falls back to a public demo endpoint so the bot can run
# out-of-the-box, but you should use your own provider for anything serious.
RPC_URL = os.getenv("RPC_URL", "https://eth.llamarpc.com")

CHAIN_ID = 1  # Ethereum mainnet

# ---------------------------------------------------------------------------
# Wallet (DEMO ONLY — never commit a real key)
# ---------------------------------------------------------------------------

# Load the private key from the environment. Left unset by default so the
# bot runs in read-only / simulation mode out of the box.
#
#   PowerShell:  $env:WALLET_PRIVATE_KEY = "0xyourkeyhere"
#   bash:        export WALLET_PRIVATE_KEY="0xyourkeyhere"
#
# This value is only ever used to derive a public address for display
# purposes in this demo — executor.py is hard-coded to simulate, never sign.
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", "")

# Address to display/track when no key is configured.
DEMO_WALLET_ADDRESS = "0x0000000000000000000000000000000000dEaD"

# ---------------------------------------------------------------------------
# DEX contract addresses (mainnet)
# ---------------------------------------------------------------------------

UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
UNISWAP_V3_QUOTER = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"

# Fee tiers to check on V3, in hundredths of a bip (500 = 0.05%, etc).
UNISWAP_V3_FEE_TIERS = [100, 500, 3000, 10000]

# ---------------------------------------------------------------------------
# Tokens to scan (symbol -> checksum address)
# ---------------------------------------------------------------------------

TOKENS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}

# Pairs to actively monitor for arbitrage.
WATCHED_PAIRS = [
    ("WETH", "USDC"),
    ("WETH", "USDT"),
    ("WETH", "DAI"),
    ("WBTC", "WETH"),
    ("USDC", "USDT"),
]

# ---------------------------------------------------------------------------
# Strategy parameters
# ---------------------------------------------------------------------------

# Minimum gross spread (in %) between two venues before we even consider it.
MIN_SPREAD_PCT = 0.30

# Minimum estimated net profit in USD after estimated gas + fees.
MIN_PROFIT_USD = 25.0

# Trade size to simulate quotes with, in the "in" token's smallest unit
# multiplier (this demo just uses whole-token notional amounts).
SIMULATED_TRADE_SIZE = {
    "WETH": 5,
    "WBTC": 0.3,
    "USDC": 10_000,
    "USDT": 10_000,
    "DAI": 10_000,
}

# How often to poll for new opportunities, in seconds.
SCAN_INTERVAL_SECONDS = 12

# Estimated gas units for a two-leg arbitrage swap (rough heuristic).
ESTIMATED_GAS_UNITS = 280_000

# ---------------------------------------------------------------------------
# Execution mode
# ---------------------------------------------------------------------------

# This demo bot NEVER sets this to True from code — executor.py always
# simulates. It's here so the intent is explicit and easy to audit.
DRY_RUN = True
