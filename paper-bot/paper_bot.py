#!/usr/bin/env python3
"""
Paper-trading BTC "gap finder" (fake money only).

Every tick it reads the best buy/sell price for BTC/USDT on several exchanges,
looks for a gap (buy cheap on one, sell higher on another), subtracts fees,
waits a little to mimic real-world delay, re-checks the price, and only then
"trades" with a fake wallet.

No API keys. No real orders. Public price data only.

Run:
    python paper_bot.py              # live prices (needs internet)
    python paper_bot.py --demo       # fake prices, works offline
    python paper_bot.py --help       # all options
"""
import argparse
import csv
import json
import random
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Approximate base-tier TAKER fees (fraction, 0.001 = 0.1%). Check your own account.
FEES = {
    "binance": 0.0010,
    "okx": 0.0010,
    "bybit": 0.0010,
    "kraken": 0.0040,
    "coinbase": 0.0060,
}


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "paper-bot/1.0"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)


def binance():
    d = _get_json("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT")
    return float(d["bidPrice"]), float(d["askPrice"])


def okx():
    d = _get_json("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT")["data"][0]
    return float(d["bidPx"]), float(d["askPx"])


def bybit():
    d = _get_json("https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT")
    t = d["result"]["list"][0]
    return float(t["bid1Price"]), float(t["ask1Price"])


def kraken():
    d = _get_json("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT")["result"]
    t = next(iter(d.values()))
    return float(t["b"][0]), float(t["a"][0])


def coinbase():
    d = _get_json("https://api.exchange.coinbase.com/products/BTC-USDT/ticker")
    return float(d["bid"]), float(d["ask"])


LIVE = {"binance": binance, "okx": okx, "bybit": bybit, "kraken": kraken, "coinbase": coinbase}


class DemoMarket:
    """Fake prices: one shared random walk + small per-exchange noise."""

    def __init__(self):
        self.mid = 65000.0

    def step(self):
        self.mid *= 1 + random.gauss(0, 0.0003)

    def quote(self, name):
        # Noise is exaggerated vs. real markets so you can see trades happen.
        m = self.mid * (1 + random.gauss(0, 0.0006))
        half_spread = m * 0.00005
        return m - half_spread, m + half_spread


def fetch_all(names, demo, pool):
    """Return {exchange: (bid, ask)} for every exchange that answered."""
    if demo:
        return {n: demo.quote(n) for n in names}
    futures = {n: pool.submit(LIVE[n]) for n in names}
    out = {}
    for n, f in futures.items():
        try:
            out[n] = f.result()
        except Exception:
            pass  # exchange blocked/slow this tick; skip it
    return out


def best_gap(quotes):
    """Find the best 'buy on A, sell on B' pair. Returns (buy_ex, sell_ex, gross, net)."""
    best = None
    for buy_ex, (_, ask) in quotes.items():
        for sell_ex, (bid, _) in quotes.items():
            if buy_ex == sell_ex:
                continue
            gross = (bid - ask) / ask
            net = gross - FEES[buy_ex] - FEES[sell_ex]
            if best is None or net > best[3]:
                best = (buy_ex, sell_ex, gross, net)
    return best


C = {"g": "\033[92m", "r": "\033[91m", "y": "\033[93m", "d": "\033[90m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def pct(x):
    return f"{x * 100:+.3f}%"


def main():
    p = argparse.ArgumentParser(description="Paper-trading BTC gap finder (fake money).")
    p.add_argument("--demo", action="store_true", help="use fake prices (no internet needed)")
    p.add_argument("--start", type=float, default=68.0, help="starting fake balance in USDT (default 68)")
    p.add_argument("--interval", type=float, default=1.0, help="seconds between checks (default 1)")
    p.add_argument("--latency", type=float, default=0.3, help="seconds between spotting a gap and 'executing' (default 0.3)")
    p.add_argument("--min-edge", type=float, default=0.0005, help="min net profit fraction to trade (default 0.0005 = 0.05%%)")
    p.add_argument("--minutes", type=float, default=5, help="how long to run (default 5)")
    p.add_argument("--exchanges", default=",".join(LIVE), help="comma list, default: all")
    p.add_argument("--log", default="trades.csv", help="CSV file for every check (default trades.csv)")
    a = p.parse_args()

    names = [n.strip() for n in a.exchanges.split(",") if n.strip() in LIVE]
    demo = DemoMarket() if a.demo else None
    pool = ThreadPoolExecutor(max_workers=len(names))

    balance = a.start
    stats = dict(ticks=0, gross_gaps=0, net_gaps=0, vanished=0, trades=0, wins=0, best_net=None)
    end = time.time() + a.minutes * 60

    mode = "DEMO (fake prices, exaggerated gaps)" if demo else "LIVE prices, FAKE money"
    print(f"{C['b']}Paper bot · {mode} · start ${balance:.2f} · {', '.join(names)}{C['x']}")
    print(f"{C['d']}Ctrl+C to stop early. Logging to {a.log}{C['x']}\n")

    with open(a.log, "w", newline="") as fh:
        log = csv.writer(fh)
        log.writerow(["time", "buy_on", "sell_on", "gross_gap", "net_gap", "action", "pnl", "balance"])
        try:
            while time.time() < end:
                t0 = time.time()
                if demo:
                    demo.step()
                quotes = fetch_all(names, demo, pool)
                if len(quotes) < 2:
                    print(f"{C['y']}Only {len(quotes)} exchange(s) answered, waiting...{C['x']}")
                    time.sleep(a.interval)
                    continue

                stats["ticks"] += 1
                buy_ex, sell_ex, gross, net = best_gap(quotes)
                stats["best_net"] = net if stats["best_net"] is None else max(stats["best_net"], net)
                if gross > 0:
                    stats["gross_gaps"] += 1
                action, pnl = "skip", 0.0
                stamp = datetime.now().strftime("%H:%M:%S")

                if net >= a.min_edge:
                    stats["net_gaps"] += 1
                    # Real life: by the time your order lands, prices moved. Re-check.
                    time.sleep(a.latency)
                    if demo:
                        demo.step()
                    again = fetch_all([buy_ex, sell_ex], demo, pool)
                    if len(again) == 2:
                        ask = again[buy_ex][1]
                        bid = again[sell_ex][0]
                        real_net = (bid - ask) / ask - FEES[buy_ex] - FEES[sell_ex]
                        pnl = balance * real_net
                        balance += pnl
                        stats["trades"] += 1
                        stats["wins"] += pnl > 0
                        action = "trade"
                        color = C["g"] if pnl > 0 else C["r"]
                        print(f"{stamp} {color}TRADE buy {buy_ex} → sell {sell_ex} | "
                              f"saw {pct(net)} got {pct(real_net)} | pnl ${pnl:+.4f} | bal ${balance:.4f}{C['x']}")
                    else:
                        stats["vanished"] += 1
                        action = "missed"
                else:
                    print(f"{C['d']}{stamp} best: buy {buy_ex:8} sell {sell_ex:8} "
                          f"gap {pct(gross)} after fees {pct(net)}  bal ${balance:.4f}{C['x']}")

                log.writerow([stamp, buy_ex, sell_ex, f"{gross:.6f}", f"{net:.6f}", action, f"{pnl:.6f}", f"{balance:.6f}"])
                fh.flush()
                time.sleep(max(0, a.interval - (time.time() - t0)))
        except KeyboardInterrupt:
            pass

    s = stats
    n = max(s["ticks"], 1)
    print(f"\n{C['b']}──── Summary ────{C['x']}")
    print(f"Checks made             : {s['ticks']}")
    print(f"Any price gap (pre-fee) : {s['gross_gaps']}  ({s['gross_gaps'] / n:.0%})")
    print(f"Gap big enough after fee: {s['net_gaps']}  ({s['net_gaps'] / n:.0%})")
    print(f"Trades taken            : {s['trades']}  (wins {s['wins']})")
    print(f"Best edge seen after fee: {pct(s['best_net']) if s['best_net'] is not None else 'n/a'}")
    color = C["g"] if balance >= a.start else C["r"]
    print(f"Balance                 : ${a.start:.2f} → {color}${balance:.4f}{C['x']}  ({(balance / a.start - 1):+.2%})")
    print(f"{C['d']}Not included: withdrawal/transfer fees, slippage on bigger sizes, frozen funds on 2 exchanges.{C['x']}")


if __name__ == "__main__":
    main()
