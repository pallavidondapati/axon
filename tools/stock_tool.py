from langchain_core.tools import tool
import yfinance as yf

@tool
def get_stock_price(symbol: str) -> str:
    """Get current stock price and information for any stock symbol. Use when user asks about stock price, market cap, or company financials. Example symbols: AAPL, GOOGL, TSLA, RELIANCE.NS, TCS.NS"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")
        
        current_price = hist['Close'].iloc[-1] if not hist.empty else info.get('currentPrice', 'N/A')
        
        return f"""
        Company: {info.get('longName', symbol)}
        Symbol: {symbol.upper()}
        Current Price: {current_price:.2f} {info.get('currency', 'USD')}
        Market Cap: {info.get('marketCap', 'N/A')}
        52 Week High: {info.get('fiftyTwoWeekHigh', 'N/A')}
        52 Week Low: {info.get('fiftyTwoWeekLow', 'N/A')}
        P/E Ratio: {info.get('trailingPE', 'N/A')}
        """
    except Exception as e:
        return f"Could not fetch stock data for {symbol}: {str(e)}"