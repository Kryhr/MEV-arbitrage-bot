# MEV Arbitrage Bot

Scans Uniswap V2 and V3 on Ethereum mainnet for cross-venue price gaps
and reports arbitrage opportunities.

This is a demo built to show the scan/evaluate/execute loop an MEV bot
uses. It reads on-chain state and simulates execution, but it does not
sign or broadcast anything - see "what this doesn't do" below.

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

## What this doesn't do

- Doesn't build, sign, or send a transaction. `executor.py` only prints
- Doesn't account for slippage or getting front-run
- No Flashbots bundling or private relay
- No flash loans or multi-hop routing
- The reads aren't atomic, by the time you'd act on a quote the pool
  state has probably already moved

Turning this into something that actually trades would need a signer,
slippage-protected tx building, simulation against the exact block
you're targeting, competitive gas bidding, and realistically a private
relay so you don't just get front-run. None of that is here.

## Disclaimer

Educational project, not a working trading product and not financial
advice. Real MEV/arbitrage trading involves smart contract risk, gas
auctions, and competition from other bots, and you can lose money
quickly. If you build on top of this to add live trading, use a burner
wallet, never commit a private key, and know what the code you're
running actually does. No liability accepted for anything built on top
of this.

## License

MIT, see [LICENSE](LICENSE).
