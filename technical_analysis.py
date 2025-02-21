import ccxt
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import config

# 📌 اتصال به Binance با API شخصی
exchange = ccxt.binance({
    'apiKey': config.BINANCE_API_KEY,
    'secret': config.BINANCE_API_SECRET,
    'enableRateLimit': True
})

# 📌 تابع دریافت اطلاعات بازار
def fetch_market_data(pair, timeframe='4h', limit=200):
    try:
        candles = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        return str(e)

# 📌 شناسایی حمایت و مقاومت قوی
def find_support_resistance(df, price):
    df_last = df.tail(120)
    pivots = []
    window_size = len(df_last) // 10
    
    for i in range(window_size, len(df_last) - window_size):
        if df_last['low'][i] == min(df_last['low'][i - window_size:i + window_size]):
            pivots.append(('support', df_last.index[i], df_last['low'][i]))
        if df_last['high'][i] == max(df_last['high'][i - window_size:i + window_size]):
            pivots.append(('resistance', df_last.index[i], df_last['high'][i]))
    
    supports = sorted([p[2] for p in pivots if p[0] == 'support' and p[2] < price], reverse=True)[:3]
    resistances = sorted([p[2] for p in pivots if p[0] == 'resistance' and p[2] > price])[:3]
    
    return supports, resistances

# 📌 تشخیص روند بازار
def determine_trend(df):
    recent_highs = df['high'].rolling(window=50).max()
    recent_lows = df['low'].rolling(window=50).min()
    
    if recent_highs.iloc[-1] > recent_highs.iloc[-50] and recent_lows.iloc[-1] > recent_lows.iloc[-50]:
        return "📈 روند صعودی - کف‌ها و سقف‌ها در حال افزایش هستند"
    elif recent_highs.iloc[-1] < recent_highs.iloc[-50] and recent_lows.iloc[-1] < recent_lows.iloc[-50]:
        return "📉 روند نزولی - کف‌ها و سقف‌ها در حال کاهش هستند"
    else:
        return "🔁 روند خنثی - قیمت در یک محدوده نوسان می‌کند"

# 📌 رسم چارت و ارسال به تلگرام با واترمارک
def plot_advanced_chart(pair, df, supports, resistances):
    df_last = df.tail(200)
    mc = mpf.make_marketcolors(up='green', down='red', wick={'up':'green', 'down':'red'}, edge={'up':'green', 'down':'red'})
    s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc)
    fig, ax = mpf.plot(df_last, type='candle', style=s, title=f"📊 چارت {pair}", ylabel='Price', returnfig=True)

    # رسم خطوط حمایت
    for level in supports:
        ax[0].axhline(y=level, color='blue', linestyle='dashed', linewidth=1.5, alpha=0.7, label="Support")

    # رسم خطوط مقاومت
    for level in resistances:
        ax[0].axhline(y=level, color='red', linestyle='dashed', linewidth=1.5, alpha=0.7, label="Resistance")

    # **✅ اضافه کردن واترمارک به‌صورت پس‌زمینه**
    ax[0].text(0.5, 0.5, "AFSalehi Analysis", fontsize=40, color='gray', alpha=0.3,
               ha='center', va='center', transform=ax[0].transAxes, fontweight='bold', rotation=30)

    chart_path = "advanced_chart.png"
    fig.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chart_path
