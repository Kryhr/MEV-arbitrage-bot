"""
scanner.py

Scans Uniswap V2 and V3 for price discrepancies on a watchlist of token
pairs and yields candidate arbitrage opportunities.

This module only reads on-chain state (via eth_call through Web3) — it
never sends a transaction. Prices are pulled by simulating a swap quote
against each venue's router/quoter contracts.
"""

import time
from dataclasses import dataclass
from typing import Optional

from web3 import Web3

import config

# Minimal ABIs — just the read-only functions this bot actually calls.
UNISWAP_V2_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "reserve0", "type": "uint112"},
            {"name": "reserve1", "type": "uint112"},
            {"name": "blockTimestampLast", "type": "uint32"},
        ],
        "type": "function",
    },
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

UNISWAP_V2_FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "type": "function",
    }
]

UNISWAP_V3_QUOTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
        ],
        "name": "quoteExactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


@dataclass
class Quote:
    venue: str
    pair: str
    price: float          # price of token_out per 1 token_in
    fee_tier: Optional[int] = None


@dataclass
class Opportunity:
    pair: str
    buy_venue: str
    sell_venue: str
    buy_price: float
    sell_price: float
    spread_pct: float
    timestamp: float


class Scanner:
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.v2_factory = w3.eth.contract(
            address=Web3.to_checksum_address(config.UNISWAP_V2_FACTORY),
            abi=UNISWAP_V2_FACTORY_ABI,
        )
        self.v3_quoter = w3.eth.contract(
            address=Web3.to_checksum_address(config.UNISWAP_V3_QUOTER),
            abi=UNISWAP_V3_QUOTER_ABI,
        )
        self._pair_cache = {}

    def _get_v2_pair_contract(self, token_a: str, token_b: str):
        cache_key = (token_a, token_b)
        if cache_key in self._pair_cache:
            return self._pair_cache[cache_key]

        pair_address = self.v2_factory.functions.getPair(
            Web3.to_checksum_address(config.TOKENS[token_a]),
            Web3.to_checksum_address(config.TOKENS[token_b]),
        ).call()

        if int(pair_address, 16) == 0:
            self._pair_cache[cache_key] = None
            return None

        contract = self.w3.eth.contract(address=pair_address, abi=UNISWAP_V2_PAIR_ABI)
        self._pair_cache[cache_key] = contract
        return contract

    def get_v2_price(self, token_in: str, token_out: str) -> Optional[Quote]:
        """Read Uniswap V2 reserves and derive a spot price."""
        pair = self._get_v2_pair_contract(token_in, token_out)
        if pair is None:
            return None

        reserve0, reserve1, _ = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()

        in_addr = Web3.to_checksum_address(config.TOKENS[token_in])
        if token0.lower() == in_addr.lower():
            reserve_in, reserve_out = reserve0, reserve1
        else:
            reserve_in, reserve_out = reserve1, reserve0

        if reserve_in == 0:
            return None

        price = reserve_out / reserve_in
        return Quote(venue="uniswap_v2", pair=f"{token_in}/{token_out}", price=price)

    def get_v3_price(self, token_in: str, token_out: str) -> Optional[Quote]:
        """Query the V3 quoter across fee tiers and keep the best quote."""
        best_quote = None
        amount_in = self._notional_amount_wei(token_in)

        for fee in config.UNISWAP_V3_FEE_TIERS:
            try:
                amount_out = self.v3_quoter.functions.quoteExactInputSingle(
                    Web3.to_checksum_address(config.TOKENS[token_in]),
                    Web3.to_checksum_address(config.TOKENS[token_out]),
                    fee,
                    amount_in,
                    0,
                ).call()
            except Exception:
                # No pool at this fee tier, or insufficient liquidity — skip.
                continue

            price = amount_out / amount_in
            if best_quote is None or price > best_quote.price:
                best_quote = Quote(venue="uniswap_v3", pair=f"{token_in}/{token_out}", price=price, fee_tier=fee)

        return best_quote

    def _notional_amount_wei(self, token: str) -> int:
        size = config.SIMULATED_TRADE_SIZE.get(token, 1)
        decimals = 6 if token in ("USDC", "USDT") else 8 if token == "WBTC" else 18
        return int(size * (10 ** decimals))

    def find_opportunities(self):
        """Yield an Opportunity for every watched pair with a large enough spread."""
        opportunities = []

        for token_a, token_b in config.WATCHED_PAIRS:
            v2_quote = self.get_v2_price(token_a, token_b)
            v3_quote = self.get_v3_price(token_a, token_b)

            quotes = [q for q in (v2_quote, v3_quote) if q is not None]
            if len(quotes) < 2:
                continue

            best_buy = min(quotes, key=lambda q: q.price)
            best_sell = max(quotes, key=lambda q: q.price)

            if best_buy.venue == best_sell.venue:
                continue

            spread_pct = ((best_sell.price - best_buy.price) / best_buy.price) * 100

            if spread_pct >= config.MIN_SPREAD_PCT:
                opportunities.append(
                    Opportunity(
                        pair=f"{token_a}/{token_b}",
                        buy_venue=best_buy.venue,
                        sell_venue=best_sell.venue,
                        buy_price=best_buy.price,
                        sell_price=best_sell.price,
                        spread_pct=spread_pct,
                        timestamp=time.time(),
                    )
                )

        return opportunities
