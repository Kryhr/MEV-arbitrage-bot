#!/usr/bin/env python3
"""
bot.py

Main entry point for the MEV arbitrage bot demo.

Connects to Ethereum over Web3, repeatedly scans a watchlist of token
pairs across Uniswap V2 and V3 for price discrepancies, and "executes"
(simulates) any opportunity that clears the configured profit threshold.

This bot NEVER sends a transaction — see executor.py for details. It's a
portfolio piece demonstrating the scan -> evaluate -> execute loop that a
real MEV bot would use, with the actually dangerous part (signing and
broadcasting) deliberately left out.

Usage:
    python bot.py            # run continuously
    python bot.py --once     # run a single scan pass and exit
"""

import argparse
import sys
import time

from web3 import Web3

import config
import executor
from scanner import Scanner


def connect() -> Web3:
    w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
    if not w3.is_connected():
        print(f"[ERROR] Could not connect to RPC endpoint: {config.RPC_URL}")
        sys.exit(1)
    return w3


def get_wallet_address(w3: Web3) -> str:
    if config.WALLET_PRIVATE_KEY:
        try:
            account = w3.eth.account.from_key(config.WALLET_PRIVATE_KEY)
            return account.address
        except Exception:
            print("[WARN] WALLET_PRIVATE_KEY is set but invalid — falling back to demo address.")
    return config.DEMO_WALLET_ADDRESS


def get_eth_price_usd(w3: Web3) -> float:
    """
    Rough ETH/USD reference price for gas-cost math, derived from the
    on-chain WETH/USDC pool this bot already scans. Falls back to a static
    estimate if that read fails for any reason.
    """
    try:
        scanner = Scanner(w3)
        quote = scanner.get_v2_price("WETH", "USDC")
        if quote and quote.price > 0:
            return quote.price
    except Exception:
        pass
    return 2500.0


def run_scan_pass(w3: Web3, scanner: Scanner, eth_price_usd: float) -> int:
    opportunities = scanner.find_opportunities()

    if not opportunities:
        print(f"[{time.strftime('%H:%M:%S')}] No opportunities above {config.MIN_SPREAD_PCT}% spread this pass.")
        return 0

    executed = 0
    for opp in opportunities:
        result = executor.execute(w3, opp, eth_price_usd=eth_price_usd)
        if result.success:
            executed += 1

    return executed


def main():
    parser = argparse.ArgumentParser(description="MEV arbitrage bot (demo — simulation only)")
    parser.add_argument("--once", action="store_true", help="run a single scan pass and exit")
    args = parser.parse_args()

    print("=" * 60)
    print("  MEV Arbitrage Bot — DEMO / SIMULATION MODE")
    print("  No transactions will be signed or broadcast.")
    print("=" * 60)

    w3 = connect()
    wallet_address = get_wallet_address(w3)
    eth_price_usd = get_eth_price_usd(w3)

    print(f"Connected: {config.RPC_URL}")
    print(f"Chain ID:  {w3.eth.chain_id}")
    print(f"Wallet:    {wallet_address}")
    print(f"Watching:  {len(config.WATCHED_PAIRS)} pairs on Uniswap V2/V3")
    print(f"ETH/USD ref price: ${eth_price_usd:,.2f}")
    print()

    scanner = Scanner(w3)

    if args.once:
        run_scan_pass(w3, scanner, eth_price_usd)
        return

    try:
        while True:
            run_scan_pass(w3, scanner, eth_price_usd)
            time.sleep(config.SCAN_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
