# 🧪 Paper BTC Gap Bot

Checks if the "$68 → $750K arbitrage bot" idea actually works, using **fake money**.

- ✅ Public prices only: **no API keys, no real orders**
- ✅ Python standard library only, nothing to install
- 📊 Exchanges: Binance, OKX, Bybit, Kraken, Coinbase (BTC/USDT)

## How it works

```
every 1s ──► get best buy/sell price from 5 exchanges
              │
              ▼
     find cheapest ASK (buy) vs highest BID (sell)
              │
     gap − fees ≥ 0.05% ? ──no──► skip (grey line)
              │ yes
              ▼
     wait 0.3s (real-life delay) ──► re-check prices
              │
              ▼
     "trade" with fake wallet ──► green = profit, red = loss
```

## Run it

```bash
python paper_bot.py --demo          # fake prices, works offline
python paper_bot.py                 # live prices, fake money, 5 minutes
python paper_bot.py --minutes 60    # run for an hour
python paper_bot.py --latency 1     # slower, like a phone/iPad setup
python paper_bot.py --exchanges binance,okx,bybit
```

Every check is saved to `trades.csv`, so you can open it in Excel or Google Sheets.

## Reading the output

```
11:56:38 best: buy binance sell okx  gap +0.212% after fees +0.012%   ← grey: looked at it, skipped
11:56:36 TRADE buy bybit → sell binance | saw +0.076% got -0.290%    ← red: gap closed before "order" landed
```

**`saw` vs `got`** is the main lesson. The gap you spot often disappears by the time you act.

## Not simulated (real life is harder)

- Withdrawal and transfer fees between exchanges
- Needing money parked on **both** exchanges at once
- Slippage on bigger orders
- Fee numbers are approximate base-tier taker fees. Edit `FEES` at the top of the file to match your account.

> If an exchange is blocked in your country, it's skipped automatically. Use `--exchanges` to choose which ones to check.
