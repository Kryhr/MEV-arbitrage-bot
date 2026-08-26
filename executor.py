"""
"Executes" arbitrage opportunities found by scanner.py.

Nothing in here signs or broadcasts a transaction - there's no signer
and no call to eth_sendRawTransaction anywhere in this file. It estimates
gas and profit, prints a summary, and returns a result object, which is
as far as this demo goes.
"""

import config
from scanner import Opportunity
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    success: bool
    opportunity: Opportunity
    estimated_gas_cost_usd: float
    estimated_net_profit_usd: float
    simulated_tx_hash: str


def estimate_gas_cost_usd(w3, eth_price_usd):
    try:
        gas_price_wei = w3.eth.gas_price
    except Exception:
        gas_price_wei = 20_000_000_000  # 20 gwei fallback

    gas_cost_eth = (gas_price_wei * config.ESTIMATED_GAS_UNITS) / 1e18
    return gas_cost_eth * eth_price_usd


def estimate_profit_usd(opportunity, trade_size_usd, gas_cost_usd):
    gross_profit = trade_size_usd * (opportunity.spread_pct / 100)
    return gross_profit - gas_cost_usd


def _fake_tx_hash(opportunity):
    # placeholder for the console output - not a real tx hash, nothing broadcast
    seed = f"{opportunity.pair}{opportunity.buy_venue}{opportunity.sell_venue}{opportunity.timestamp}"
    return "0x" + format(abs(hash(seed)) % (16 ** 64), "064x")


def execute(w3, opportunity, eth_price_usd=2500.0):
    if not config.DRY_RUN:
        # this branch shouldn't be reachable - there's no live execution path
        raise RuntimeError("DRY_RUN disabled but no live trading path exists in this repo")

    trade_size_usd = config.SIMULATED_TRADE_SIZE.get(opportunity.pair.split("/")[0], 1) * eth_price_usd
    gas_cost_usd = estimate_gas_cost_usd(w3, eth_price_usd)
    net_profit_usd = estimate_profit_usd(opportunity, trade_size_usd, gas_cost_usd)
    success = net_profit_usd >= config.MIN_PROFIT_USD
    tx_hash = _fake_tx_hash(opportunity)

    print(f"[{opportunity.pair}] buy {opportunity.buy_venue} @ {opportunity.buy_price:.6f} "
          f"-> sell {opportunity.sell_venue} @ {opportunity.sell_price:.6f} "
          f"(spread {opportunity.spread_pct:.3f}%)")
    print(f"  gas est: ${gas_cost_usd:,.2f}  net profit est: ${net_profit_usd:,.2f}")

    if success:
        print(f"  Trade executed. tx: {tx_hash}")
    else:
        print("  skipped, profit below MIN_PROFIT_USD")

    return ExecutionResult(
        success=success,
        opportunity=opportunity,
        estimated_gas_cost_usd=gas_cost_usd,
        estimated_net_profit_usd=net_profit_usd,
        simulated_tx_hash=tx_hash,
    )
