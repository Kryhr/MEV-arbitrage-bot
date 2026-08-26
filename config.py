import os

# --- network ---

RPC_URL = os.getenv("RPC_URL", "https://eth.llamarpc.com")
CHAIN_ID = 1

# --- wallet ---
# key is read from env, not hardcoded. leave it blank to run in read-only mode.
# PowerShell:  $env:WALLET_PRIVATE_KEY = "0xyourkeyhere"
# bash:        export WALLET_PRIVATE_KEY="0xyourkeyhere"
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", "")
DEMO_WALLET_ADDRESS = "0x0000000000000000000000000000000000dEaD"

# --- dex contracts (mainnet) ---

UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
UNISWAP_V3_QUOTER = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"

UNISWAP_V3_FEE_TIERS = [100, 500, 3000, 10000]

# --- tokens ---

TOKENS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}

WATCHED_PAIRS = [
    ("WETH", "USDC"),
    ("WETH", "USDT"),
    ("WETH", "DAI"),
    ("WBTC", "WETH"),
    ("USDC", "USDT"),
]

# --- strategy params ---

MIN_SPREAD_PCT = 0.30          # ignore anything below this raw spread
MIN_PROFIT_USD = 25.0          # ignore anything that doesn't clear gas by at least this much

SIMULATED_TRADE_SIZE = {
    "WETH": 5,
    "WBTC": 0.3,
    "USDC": 10_000,
    "USDT": 10_000,
    "DAI": 10_000,
}

SCAN_INTERVAL_SECONDS = 12
ESTIMATED_GAS_UNITS = 280_000   # rough two-leg swap estimate

# executor.py always simulates regardless of this flag - it's just here
# so the intent is obvious when reading the code.
DRY_RUN = True
