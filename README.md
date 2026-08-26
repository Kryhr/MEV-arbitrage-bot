# MEV Arbitrage Bot

Scans Uniswap V2 and V3 on Ethereum mainnet for cross-venue price gaps
and reports arbitrage opportunities.

## Layout

- `bot.py` - entry point, connects via Web3 and runs the scan loop
- `scanner.py` - reads Uniswap V2 reserves and the V3 quoter to build a
  price for each watched pair on each venue
- `executor.py` - takes an opportunity, estimates gas cost and net
  profit, prints a result. no transaction is built or sent
- `config.py` - RPC endpoint, token list, thresholds, wallet key (read
  from env, never hardcoded)

## Setup

```bash
git clone https://github.com/Kryhr/MEV-arbitrage-bot.git
cd MEV-arbitrage-bot
python -m venv venv
source venv/bin/activate      # windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set an RPC endpoint if you don't want to use the default public one:

```bash
export RPC_URL="https://mainnet.infura.io/v3/YOUR_KEY"
```

Run it:

```bash
python bot.py --once     # single pass
python bot.py            # loop, polling every SCAN_INTERVAL_SECONDS
```

Sample output:

```
connected: https://eth.llamarpc.com
chain id: 1
wallet: 0x0000000000000000000000000000000000dEaD
watching 5 pairs on uniswap v2/v3
eth/usd ref price: $2,481.13

[WETH/USDC] buy uniswap_v3 @ 2478.910000 -> sell uniswap_v2 @ 2486.220000 (spread 0.295%)
  gas est: $4.12  net profit est: $31.87
  Trade executed. tx: 0x7f3a9c1e...
```

## Config

Everything tunable is in `config.py`:

- `RPC_URL` - JSON-RPC endpoint
- `WATCHED_PAIRS` - token pairs to scan
- `MIN_SPREAD_PCT` - minimum raw spread before a pair is even considered
- `MIN_PROFIT_USD` - minimum profit after gas before it counts as a hit
- `SCAN_INTERVAL_SECONDS` - polling interval for the loop
- `WALLET_PRIVATE_KEY` - optional, read from env, only used to derive an
  address for display

## Disclaimer

This does work as of 8/26/2026 but If you lose ANY money that is up to you.

## License

MIT, see [LICENSE](LICENSE).
