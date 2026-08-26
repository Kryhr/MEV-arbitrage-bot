import os

# RPC endpoint - use environment variable or fallback
RPC_URL = os.getenv("RPC_URL", "https://cloudflare-eth.com/")

# Wallet config (for demo purposes only)
DEMO_WALLET_ADDRESS = "0x0000000000000000000000000000000000dEaD"
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", "")

# Token pairs to watch
WATCHED_PAIRS = [
    ("WETH", "USDC"),
    ("WETH", "DAI"),
    ("WETH", "USDT"),
]

# Thresholds
MIN_SPREAD_PCT = 0.3
MIN_PROFIT_USD = 10.0
SCAN_INTERVAL_SECONDS = 10