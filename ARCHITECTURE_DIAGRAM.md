# 🏗️ FXBot Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FXBot Trading System                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐            ┌────────▼────────┐
            │  Backtesting   │            │  Live Trading   │
            │     Mode       │            │      Mode       │
            └───────┬────────┘            └────────┬────────┘
                    │                               │
        ┌───────────┴──────────┐        ┌──────────┴──────────┐
        │                      │        │                     │
┌───────▼────────┐   ┌────────▼──────┐ │  ┌─────────────────▼──────────┐
│  Historical    │   │   Strategy    │ │  │   Real-time Data Stream    │
│  Data Loader   │   │  Backtester   │ │  │   (OANDA v20 API)          │
└───────┬────────┘   └────────┬──────┘ │  └─────────────────┬──────────┘
        │                     │        │                    │
        └──────────┬──────────┘        │         ┌──────────┴──────────┐
                   │                   │         │                     │
           ┌───────▼────────┐          │  ┌──────▼──────┐    ┌────────▼────────┐
           │   Performance  │          │  │   Signal    │    │   Position      │
           │   Metrics      │          │  │  Generator  │    │   Manager       │
           └────────────────┘          │  └──────┬──────┘    └────────┬────────┘
                                       │         │                    │
                                       │  ┌──────▼────────────────────▼────┐
                                       │  │    Risk Management Engine      │
                                       │  │  - Position Sizing             │
                                       │  │  - Stop Loss / Take Profit     │
                                       │  │  - Portfolio Limits            │
                                       │  └──────┬─────────────────────────┘
                                       │         │
                                       │  ┌──────▼──────────────────────────┐
                                       │  │    Order Execution Engine       │
                                       │  │  - Market Orders                │
                                       │  │  - Limit Orders                 │
                                       │  │  - Position Tracking            │
                                       │  └──────┬──────────────────────────┘
                                       │         │
                                       └─────────┴──────────────────────────┐
                                                 │                          │
                                        ┌────────▼────────┐      ┌──────────▼─────────┐
                                        │   GUI Display   │      │  Performance       │
                                        │   - Charts      │      │  Tracking          │
                                        │   - Positions   │      │  - P&L             │
                                        │   - Logs        │      │  - Win Rate        │
                                        └─────────────────┘      │  - Sharpe Ratio    │
                                                                 └────────────────────┘
```

## Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Data Flow Architecture                                │
└─────────────────────────────────────────────────────────────────────────────┘

1. DATA ACQUISITION
   ┌──────────────┐
   │ OANDA API    │──────┐
   │ (tpqoa)      │      │
   └──────────────┘      │
                         ▼
                  ┌──────────────┐
                  │ Price Stream │
                  │ - Bid/Ask    │
                  │ - Timestamp  │
                  └──────┬───────┘
                         │
2. DATA PROCESSING       ▼
   ┌─────────────────────────────────┐
   │   Market Data Processor         │
   │   - Candle Formation            │
   │   - OHLCV Data                  │
   │   - Technical Indicators        │
   └──────────────┬──────────────────┘
                  │
3. ANALYSIS      ▼
   ┌─────────────────────────────────────────────────────┐
   │           Multi-Strategy Analyzer                   │
   ├─────────────────────────────────────────────────────┤
   │  ┌──────────────────┐  ┌─────────────────────┐     │
   │  │ Bullish Rejection│  │  Trend Following    │     │
   │  │ Blocks (40%)     │  │  (SMA) (30%)        │     │
   │  └────────┬─────────┘  └──────────┬──────────┘     │
   │           │                       │                 │
   │  ┌────────▼─────────┐  ┌─────────▼──────────┐     │
   │  │  Momentum        │  │  Mean Reversion    │     │
   │  │  (RSI) (20%)     │  │  (Bollinger) (10%) │     │
   │  └────────┬─────────┘  └──────────┬──────────┘     │
   │           │                       │                 │
   │           └───────────┬───────────┘                 │
   │                       ▼                             │
   │              ┌─────────────────┐                    │
   │              │ Weighted Score  │                    │
   │              │ Calculation     │                    │
   │              └────────┬────────┘                    │
   └───────────────────────┼─────────────────────────────┘
                           │
4. SIGNAL GENERATION       ▼
   ┌─────────────────────────────────┐
   │   Signal Decision Engine        │
   │   - BUY (score > 0.6)           │
   │   - SELL (score < -0.6)         │
   │   - HOLD (|score| <= 0.6)       │
   └──────────────┬──────────────────┘
                  │
5. RISK MANAGEMENT▼
   ┌─────────────────────────────────┐
   │   Position Sizing Calculator    │
   │   - Account Balance × Risk%     │
   │   - Stop Loss Distance          │
   │   - Max Position Limits         │
   └──────────────┬──────────────────┘
                  │
6. EXECUTION      ▼
   ┌─────────────────────────────────┐
   │   Order Execution               │
   │   - Create Market Order         │
   │   - Set Stop Loss (0.5%)        │
   │   - Set Take Profit (1%)        │
   └──────────────┬──────────────────┘
                  │
7. MONITORING     ▼
   ┌─────────────────────────────────┐
   │   Position Monitor              │
   │   - Track P&L                   │
   │   - Check Exit Conditions       │
   │   - Update GUI                  │
   └─────────────────────────────────┘
```

## Class Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Class Structure                          │
└─────────────────────────────────────────────────────────────┘

tpqoa (OANDA API Wrapper)
  │
  ├── LiveTrader (Base Live Trading Class)
  │     │
  │     ├── BasicTrader
  │     ├── PicoTrader
  │     ├── NanoTrader
  │     ├── MicroTrader
  │     ├── MiniTrader
  │     ├── FemtoTrader
  │     ├── AutoTrader
  │     ├── SMALive
  │     ├── BollingerBandsLive
  │     ├── MomentumLive
  │     └── ContrarianLive
  │
  ├── AdvancedTrader (Ultimate Interface)
  │     │
  │     └── Multi-Strategy Integration
  │           ├── Bullish Rejection Blocks
  │           ├── Trend Following
  │           ├── Momentum
  │           └── Mean Reversion
  │
  └── UltimateTrader (Standalone)
        └── Multi-Instrument Trading


Backtester (Base Backtesting Class)
  │
  ├── SMABacktest
  ├── BollingerBandsBacktest
  ├── MomentumBacktest
  ├── ContrarianBacktest
  └── MLClassificationBacktest

IterativeBase (Event-Driven Backtesting)
  │
  └── IterativeBacktest
        ├── test_sma()
        ├── test_bollinger_bands()
        ├── test_momentum()
        ├── test_contrarian()
        └── test_bullish_rejection_blocks()


GUI Classes
  │
  ├── TradingGUI (Basic)
  ├── AdvancedTradingGUI
  ├── MultiInstrumentGUI
  └── UltimateTradingInterface (Most Advanced)
        ├── AdvancedTrader
        ├── BacktestingEngine
        └── GUI Components
```

## Strategy Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│              Strategy Selection Logic                       │
└─────────────────────────────────────────────────────────────┘

Market Data Input
      │
      ▼
┌─────────────────┐
│ Analyze Market  │
│ Conditions      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Trending│ │Ranging │
│Market  │ │Market  │
└───┬────┘ └───┬────┘
    │          │
    │          └──────────┐
    │                     │
    ▼                     ▼
┌─────────────────┐  ┌──────────────────┐
│ Trend Following │  │ Mean Reversion   │
│ - SMA Cross     │  │ - Bollinger      │
│ - Momentum      │  │ - Contrarian     │
└────────┬────────┘  └────────┬─────────┘
         │                    │
         └──────────┬─────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Pattern Recognition  │
         │ - Bullish Rejection  │
         │ - Candlestick        │
         │ - Trendlines         │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Weighted Score       │
         │ Calculation          │
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌────────┐           ┌────────┐
    │ Strong │           │  Weak  │
    │ Signal │           │ Signal │
    │(>0.6)  │           │(<0.6)  │
    └───┬────┘           └───┬────┘
        │                    │
        ▼                    ▼
    ┌────────┐           ┌────────┐
    │ TRADE  │           │  HOLD  │
    └────────┘           └────────┘
```

## Risk Management Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Risk Management System                         │
└─────────────────────────────────────────────────────────────┘

Trading Signal Generated
         │
         ▼
┌─────────────────────┐
│ Check Portfolio     │
│ Constraints         │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌─────────┐
│Max Pos  │  │Max      │
│Reached? │  │Exposure?│
└────┬────┘  └────┬────┘
     │            │
     │ NO         │ NO
     └─────┬──────┘
           │
           ▼
┌──────────────────────┐
│ Calculate Position   │
│ Size                 │
│                      │
│ Size = (Balance ×    │
│         Risk%) /     │
│         Stop Loss    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Apply Limits         │
│ - Max 10% balance    │
│ - Max 10,000 units   │
│ - Min 10 units       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Set Exit Levels      │
│ - Stop Loss: -0.5%   │
│ - Take Profit: +1%   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Execute Trade        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Monitor Position     │
│ - Update P&L         │
│ - Check Exits        │
│ - Adjust if needed   │
└──────────────────────┘
```

## Data Storage & State Management

```
┌─────────────────────────────────────────────────────────────┐
│                  State Management                           │
└─────────────────────────────────────────────────────────────┘

In-Memory State
├── _positions: {}
│   └── {instrument: {type, units, entry_price, ...}}
│
├── _trade_history: []
│   └── [{instrument, type, pnl, entry_time, ...}]
│
├── _market_data: {}
│   └── {instrument: DataFrame(OHLCV)}
│
├── _trend_analysis: {}
│   └── {instrument: {strategies, score, recommendation}}
│
└── _performance_stats: {}
    └── {total_trades, win_rate, total_pnl, ...}

Configuration Files
├── config/oanda_demo.cfg
├── config/oanda_live.cfg
└── settings.json

Persistent Storage (Optional)
├── Trade logs (CSV/JSON)
├── Performance history
└── Backtest results
```

## Threading Model

```
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Threading Architecture               │
└─────────────────────────────────────────────────────────────┘

Main Thread (GUI)
    │
    ├─── Trading Thread
    │      │
    │      └─── Loop (30s cycle)
    │            ├── Get market data
    │            ├── Analyze instruments
    │            ├── Manage positions
    │            ├── Find opportunities
    │            └── Execute trades
    │
    ├─── Analysis Thread
    │      │
    │      └─── Loop (60s cycle)
    │            ├── Update performance stats
    │            ├── Analyze all instruments
    │            └── Update trend analysis
    │
    └─── GUI Update Thread
           │
           └─── Loop (continuous)
                 ├── Update charts
                 ├── Update positions display
                 ├── Update performance metrics
                 └── Log analysis messages
```

## API Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│              OANDA API Communication                        │
└─────────────────────────────────────────────────────────────┘

Application
    │
    ▼
┌─────────────────┐
│ tpqoa Wrapper   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ v20 Python SDK  │
└────────┬────────┘
         │
         ▼ HTTPS
┌─────────────────────────────────┐
│ OANDA v20 REST API              │
│ - api-fxpractice.oanda.com      │
│ - api-fxtrade.oanda.com (live)  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ OANDA Streaming API             │
│ - stream-fxpractice.oanda.com   │
│ - stream-fxtrade.oanda.com      │
└─────────────────────────────────┘

API Endpoints Used:
├── /v3/accounts/{accountID}
├── /v3/accounts/{accountID}/instruments
├── /v3/accounts/{accountID}/pricing
├── /v3/accounts/{accountID}/orders
├── /v3/accounts/{accountID}/positions
├── /v3/accounts/{accountID}/transactions
└── /v3/instruments/{instrument}/candles
```

---

## Key Design Patterns

### 1. **Strategy Pattern**
Different trading strategies implement common interface

### 2. **Observer Pattern**
GUI observes trading state changes via callbacks

### 3. **Factory Pattern**
Creating different trader types based on configuration

### 4. **Template Method**
Base classes define algorithm structure, subclasses implement details

### 5. **Singleton Pattern**
Single instance of API connection per account

---

## Performance Considerations

### **Optimization Points**:
1. **Data Caching**: Store recent candles to avoid repeated API calls
2. **Async Processing**: Threading for non-blocking operations
3. **Batch Operations**: Group API requests when possible
4. **Efficient Calculations**: Vectorized operations with pandas/numpy
5. **Memory Management**: Limit historical data retention

### **Scalability**:
- Can handle 5+ instruments simultaneously
- 30-second analysis cycles
- Real-time position monitoring
- Efficient GUI updates

---

*This architecture supports both educational learning and production trading scenarios.*
