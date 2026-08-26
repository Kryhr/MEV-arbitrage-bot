"""
executor.py

Handles "execution" of arbitrage opportunities found by scanner.py.

*** THIS MODULE NEVER SIGNS OR BROADCASTS A TRANSACTION. ***

It exists to show the shape a real executor would have (gas estimation,
slippage checks, profit-after-cost math) without any of the actually
dangerous parts — there is no code path here that reaches
`eth_sendRawTransaction` or a signer. This is intentional: this repo is a
portfolio/demo project, not a tool meant to move funds.
"""

import time
from dataclasses import dataclass

import config
from scanner import Opportunity


@dataclass
class ExecutionResult:
    success: bool
    opportunity: Opportunity
    estimated_gas_cost_usd: float
    estimated_net_profit_usd: float
    simulated_tx_hash: str


def estimate_gas_cost_usd(w3, eth_price_usd: float) -> float:
    """Rough gas cost estimate for a two-leg swap, in USD."""
    try:
        gas_price_wei = w3.eth.gas_price
    except Exception:
        gas_price_wei = 20_000_000_000  # 20 gwei fallback

    gas_cost_eth = (gas_price_wei * config.ESTIMATED_GAS_UNITS) / 1e18
    return gas_cost_eth * eth_price_usd


def estimate_profit_usd(opportunity: Opportunity, trade_size_usd: float, gas_cost_usd: float) -> float:
    """Very rough profit estimate: gross spread applied to trade size, minus gas."""
    gross_profit = trade_size_usd * (opportunity.spread_pct / 100)
    return gross_profit - gas_cost_usd


def _fake_tx_hash(opportunity: Opportunity) -> str:
    """Deterministic-looking placeholder hash for display purposes only.

    This is NOT a real transaction hash — nothing was broadcast. It exists
    purely so the console output looks like what a live bot would print.
    """
    seed = f"{opportunity.pair}-{opportunity.buy_venue}-{opportunity.sell_venue}-{opportunity.timestamp}"
    return "0x" + format(abs(hash(seed)) % (16 ** 64), "064x")


def execute(w3, opportunity: Opportunity, eth_price_usd: float = 2500.0) -> ExecutionResult:
    """
    Simulate executing an arbitrage trade for the given opportunity.

    In DRY_RUN mode (the only mode this repo supports), this:
      1. Estimates gas cost from the current network gas price.
      2. Estimates net profit after that gas cost.
      3. Prints a summary to the console.
      4. Returns an ExecutionResult — no transaction is ever built or signed.
    """
    if not config.DRY_RUN:
        # Defensive guard — this branch should be unreachable in this repo.
        raise RuntimeError(
            "DRY_RUN is disabled, but this demo executor has no live trading "
            "implementation. Refusing to proceed."
        )

    trade_size_usd = config.SIMULATED_TRADE_SIZE.get(opportunity.pair.split("/")[0], 1) * eth_price_usd
    gas_cost_usd = estimate_gas_cost_usd(w3, eth_price_usd)
    net_profit_usd = estimate_profit_usd(opportunity, trade_size_usd, gas_cost_usd)

    success = net_profit_usd >= config.MIN_PROFIT_USD
    tx_hash = _fake_tx_hash(opportunity)

    print("-" * 60)
    print(f"[SIMULATED] Arbitrage opportunity: {opportunity.pair}")
    print(f"  Buy on:   {opportunity.buy_venue:<12} @ {opportunity.buy_price:.6f}")
    print(f"  Sell on:  {opportunity.sell_venue:<12} @ {opportunity.sell_price:.6f}")
    print(f"  Spread:   {opportunity.spread_pct:.3f}%")
    print(f"  Est. gas cost:    ${gas_cost_usd:,.2f}")
    print(f"  Est. net profit:  ${net_profit_usd:,.2f}")

    if success:
        print(f"  Trade executed (simulated). tx: {tx_hash}")
    else:
        print("  Skipped — estimated profit below MIN_PROFIT_USD threshold.")
    print("-" * 60)

    return ExecutionResult(
        success=success,
        opportunity=opportunity,
        estimated_gas_cost_usd=gas_cost_usd,
        estimated_net_profit_usd=net_profit_usd,
        simulated_tx_hash=tx_hash,
    )
