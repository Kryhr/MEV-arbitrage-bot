# MEV Arbitrage Bot (Demo)

A Python bot that scans Uniswap V2 and V3 on Ethereum mainnet for
cross-venue price discrepancies and reports arbitrage opportunities in
real time.

> **This is a portfolio/demo project.** It reads on-chain state and
> simulates trade execution, but it does **not** sign or broadcast any
> transaction. See [Disclaimer](#disclaimer) below before you do anything
> with it.

## How it works

```
bot.py         entry point: connects to Ethereum, runs the scan loop
scanner.py     reads Uniswap V2 reserves + Uniswap V3 quoter to build
               a price for each watched pair on each venue
executor.py    takes an opportunity, estimates gas cost and net profit,
               and prints a "trade executed" summary — nothing is sent
config.py      RPC endpoint, token list, thresholds, wallet placeholder
```

The loop in `bot.py` is the classic three-stage MEV bot shape:

1. **Scan** — for every pair in `config.WATCHED_PAIRS`, pull a spot price
   from Uniswap V2 (via pool reserves) and Uniswap V3 (via the on-chain
   `Quoter` contract, across the standard fee tiers).
2. **Evaluate** — if the spread between the cheapest and most expensive
   venue clears `MIN_SPREAD_PCT`, estimate gas cost from the live gas
   price and compute an estimated net profit in USD.
3. **Execute** — if net profit clears `MIN_PROFIT_USD`, `executor.py`
   prints a `Trade executed` summary with a simulated transaction hash.
   No transaction is ever built, signed, or sent — see
   [What this bot does NOT do](#what-this-bot-does-not-do).

All chain reads go through a standard `web3.py` `HTTPProvider`, so any
JSON-RPC endpoint works (a public RPC, Infura, Alchemy, or your own node).

## Setup

```bash
git clone https://github.com/Kryhr/MEV-arbitrage-bot.git
cd MEV-arbitrage-bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set an RPC endpoint (optional — defaults to a public one):

```bash
export RPC_URL="https://mainnet.infura.io/v3/YOUR_KEY"   # bash
$env:RPC_URL = "https://mainnet.infura.io/v3/YOUR_KEY"    # PowerShell
```

Run it:

```bash
python bot.py --once     # single scan pass, then exit
python bot.py            # loop continuously, polling every SCAN_INTERVAL_SECONDS
```

Example output:

```
============================================================
  MEV Arbitrage Bot — DEMO / SIMULATION MODE
  No transactions will be signed or broadcast.
============================================================
Connected: https://eth.llamarpc.com
Chain ID:  1
Wallet:    0x0000000000000000000000000000000000dEaD
Watching:  5 pairs on Uniswap V2/V3
ETH/USD ref price: $2,481.13

------------------------------------------------------------
[SIMULATED] Arbitrage opportunity: WETH/USDC
  Buy on:   uniswap_v3   @ 2478.910000
  Sell on:  uniswap_v2   @ 2486.220000
  Spread:   0.295%
  Est. gas cost:    $4.12
  Est. net profit:  $31.87
  Trade executed (simulated). tx: 0x7f3a9c...
------------------------------------------------------------
```

## Configuration

Everything tunable lives in `config.py`:

| Setting | Purpose |
|---|---|
| `RPC_URL` | JSON-RPC endpoint |
| `WATCHED_PAIRS` | token pairs to scan |
| `MIN_SPREAD_PCT` | minimum raw price spread before considering a pair |
| `MIN_PROFIT_USD` | minimum estimated profit after gas before "executing" |
| `SCAN_INTERVAL_SECONDS` | polling interval for the continuous loop |
| `WALLET_PRIVATE_KEY` | optional, read from the `WALLET_PRIVATE_KEY` env var — only used to derive an address for display |

## What this bot does NOT do

This is a demo built to showcase the architecture of an MEV arbitrage
bot, not a production trading system. Notably, it does **not**:

- Build, sign, or broadcast any transaction (`executor.py` only prints)
- Account for slippage, MEV competition, or mempool front-running
- Bundle transactions via Flashbots or any other private relay
- Handle flash loans, multi-hop routing, or gas auctions
- Guarantee the on-chain reads above are race-free — by the time you'd
  act on a quote, the underlying pool state has likely moved

Turning this into something that actually trades would require, at
minimum: a signer, slippage-protected transaction building, simulation
against the exact block you intend to land in, competitive gas/priority
fee bidding, and (realistically) a private relay to avoid getting
front-run by other searchers. None of that is implemented here.

## Disclaimer

This repository is provided **for educational purposes only**, to
illustrate how an MEV arbitrage bot is structured. It is not financial
advice and not a working trading product.

- No transaction is ever signed or sent by this code.
- Real MEV/arbitrage trading involves smart contract risk, gas auctions,
  competition from other searchers and bots, and the very real
  possibility of losing money — often quickly.
- If you extend this to interact with mainnet, use a dedicated burner
  wallet, never commit a private key to source control, and understand
  the code you are running before you run it.
- The author assumes no liability for any use of this code, including
  any modified version that adds live trading capability.
