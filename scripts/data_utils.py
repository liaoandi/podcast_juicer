#!/usr/bin/env python3
"""
实时数据源模块 - 用于验证投资信号

支持的数据源：
1. Yahoo Finance - 股票价格、历史数据、财务指标
2. 可扩展其他数据源

使用方法：
    from data_utils import DataSources

    ds = DataSources()
    price = ds.get_stock_price('NVDA')
    history = ds.get_price_history('NVDA', '2025-01-15', '2025-02-03')
    change = ds.get_price_change('NVDA', '2025-01-15')
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# 尝试导入 yfinance
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class YahooFinance:
    """Yahoo Finance 数据源"""

    def __init__(self):
        if not HAS_YFINANCE:
            raise ImportError("yfinance 未安装，运行: pip install yfinance")

    def normalize_ticker(self, ticker: str) -> str:
        """
        将ticker转换为Yahoo Finance标准格式

        香港股票：00700 -> 0700.HK (保留到4位)
        上海A股：600519 -> 600519.SS
        深圳A股：000001 -> 000001.SZ
        美股：NVDA -> NVDA（保持不变）
        """
        ticker = ticker.strip().upper()

        # Reject obviously invalid tickers
        if not ticker or len(ticker) > 10:
            return ticker

        # 香港股票：5位数字，转为4位（去掉一个前导0）
        if ticker.isdigit() and len(ticker) == 5:
            # 00700 -> 0700, 00941 -> 0941
            normalized = ticker[1:]  # 直接去掉第一个字符
            return f"{normalized}.HK"

        # 香港股票：4位数字
        if ticker.isdigit() and len(ticker) == 4:
            return f"{ticker}.HK"

        # 上海A股：6位数字，以6开头
        if ticker.isdigit() and len(ticker) == 6:
            if ticker.startswith('6'):
                return f"{ticker}.SS"
            # 深圳A股：以0或3开头
            elif ticker.startswith(('0', '3')):
                return f"{ticker}.SZ"

        # 其他保持原样（如美股）
        return ticker

    def get_ticker(self, symbol: str) -> Any:
        """获取股票 Ticker 对象"""
        normalized = self.normalize_ticker(symbol)
        return yf.Ticker(normalized)

    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """
        获取当前股价

        Returns:
            {
                'symbol': 'NVDA',
                'price': 850.50,
                'currency': 'USD',
                'change': 12.30,
                'change_percent': 1.47,
                'market_cap': 2100000000000,
                'volume': 45000000,
                'timestamp': '2025-02-03 16:00:00'
            }
        """
        try:
            ticker = self.get_ticker(symbol)
            info = ticker.info

            # 获取最新价格
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

            if not price:
                # 尝试从历史数据获取
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]

            if not price:
                return None

            change = price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            return {
                'symbol': symbol,
                'price': round(price, 2),
                'currency': info.get('currency', 'USD'),
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'market_cap': info.get('marketCap'),
                'volume': info.get('volume'),
                'name': info.get('shortName', symbol),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            print(f"   ⚠️ 获取 {symbol} 价格失败: {e}")
            return None

    def get_price_history(self, symbol: str, start_date: str, end_date: str = None) -> Optional[List[Dict]]:
        """
        获取历史价格数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认今天

        Returns:
            [
                {'date': '2025-01-15', 'open': 800, 'high': 820, 'low': 795, 'close': 815, 'volume': 40000000},
                ...
            ]
        """
        try:
            ticker = self.get_ticker(symbol)

            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                return None

            result = []
            for date, row in hist.iterrows():
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume'])
                })

            return result

        except Exception as e:
            print(f"   ⚠️ 获取 {symbol} 历史数据失败: {e}")
            return None

    def get_price_change(self, symbol: str, from_date: str, to_date: str = None) -> Optional[Dict]:
        """
        计算价格变化

        Args:
            symbol: 股票代码
            from_date: 起始日期 (YYYY-MM-DD)
            to_date: 结束日期，默认今天

        Returns:
            {
                'symbol': 'NVDA',
                'from_date': '2025-01-15',
                'to_date': '2025-02-03',
                'from_price': 800.00,
                'to_price': 850.50,
                'change': 50.50,
                'change_percent': 6.31,
                'trading_days': 14
            }
        """
        try:
            history = self.get_price_history(symbol, from_date, to_date)

            if not history or len(history) < 2:
                return None

            from_price = history[0]['close']
            to_price = history[-1]['close']
            change = to_price - from_price
            change_pct = (change / from_price * 100) if from_price else 0

            return {
                'symbol': symbol,
                'from_date': history[0]['date'],
                'to_date': history[-1]['date'],
                'from_price': from_price,
                'to_price': to_price,
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'trading_days': len(history),
                'high_in_period': max(h['high'] for h in history),
                'low_in_period': min(h['low'] for h in history)
            }

        except Exception as e:
            print(f"   ⚠️ 计算 {symbol} 价格变化失败: {e}")
            return None

    def get_financials(self, symbol: str) -> Optional[Dict]:
        """
        获取财务数据

        Returns:
            {
                'symbol': 'NVDA',
                'pe_ratio': 65.5,
                'forward_pe': 45.2,
                'market_cap': 2100000000000,
                'revenue': 60000000000,
                'profit_margin': 0.55,
                'debt_to_equity': 0.41
            }
        """
        try:
            ticker = self.get_ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'revenue': info.get('totalRevenue'),
                'revenue_growth': info.get('revenueGrowth'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'book_value': info.get('bookValue'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            print(f"   ⚠️ 获取 {symbol} 财务数据失败: {e}")
            return None

    def search_ticker(self, query: str) -> List[Dict]:
        """
        搜索股票代码

        Args:
            query: 搜索关键词（公司名或代码）

        Returns:
            [{'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'}, ...]
        """
        try:
            # yfinance 没有直接的搜索 API，尝试直接查询
            ticker = yf.Ticker(query)
            info = ticker.info

            if info and info.get('symbol'):
                return [{
                    'symbol': info.get('symbol'),
                    'name': info.get('shortName', info.get('longName', query)),
                    'exchange': info.get('exchange', 'Unknown')
                }]

            return []

        except Exception:
            return []


class DataSources:
    """
    数据源聚合器

    整合多个数据源，提供统一接口
    """

    def __init__(self):
        self.yahoo = YahooFinance() if HAS_YFINANCE else None

    def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """获取当前股价"""
        if self.yahoo:
            return self.yahoo.get_current_price(symbol)
        return None

    def get_price_history(self, symbol: str, start_date: str, end_date: str = None) -> Optional[List[Dict]]:
        """获取历史价格"""
        if self.yahoo:
            return self.yahoo.get_price_history(symbol, start_date, end_date)
        return None

    def get_price_change(self, symbol: str, from_date: str, to_date: str = None) -> Optional[Dict]:
        """计算价格变化"""
        if self.yahoo:
            return self.yahoo.get_price_change(symbol, from_date, to_date)
        return None

    def get_financials(self, symbol: str) -> Optional[Dict]:
        """获取财务数据"""
        if self.yahoo:
            return self.yahoo.get_financials(symbol)
        return None

    def verify_price_prediction(self, symbol: str, prediction_date: str,
                                 prediction: str, current_date: str = None) -> Dict:
        """
        验证价格预测

        Args:
            symbol: 股票代码
            prediction_date: 预测发出的日期
            prediction: 预测内容 ('bullish', 'bearish', 'neutral', 或具体目标价)
            current_date: 验证日期，默认今天

        Returns:
            {
                'symbol': 'NVDA',
                'prediction': 'bullish',
                'prediction_date': '2025-01-15',
                'verification_date': '2025-02-03',
                'price_at_prediction': 800.00,
                'price_now': 850.50,
                'change_percent': 6.31,
                'prediction_correct': True,
                'verification_status': 'verified_correct'
            }
        """
        if not current_date:
            current_date = datetime.now().strftime('%Y-%m-%d')

        change = self.get_price_change(symbol, prediction_date, current_date)

        if not change:
            return {
                'symbol': symbol,
                'prediction': prediction,
                'prediction_date': prediction_date,
                'verification_date': current_date,
                'verification_status': 'data_unavailable',
                'error': '无法获取价格数据'
            }

        # 判断预测是否正确
        change_pct = change['change_percent']

        if prediction.lower() in ['bullish', 'buy', '看涨', '看多']:
            prediction_correct = change_pct > 0
        elif prediction.lower() in ['bearish', 'sell', '看跌', '看空']:
            prediction_correct = change_pct < 0
        elif prediction.lower() in ['neutral', 'hold', '中性', '持有']:
            prediction_correct = abs(change_pct) < 5  # 5% 以内算中性
        else:
            # 尝试解析为目标价
            try:
                target_price = float(prediction.replace('$', '').replace(',', ''))
                # 如果当前价格接近目标价（10%以内），算正确
                current_price = change['to_price']
                prediction_correct = abs(current_price - target_price) / target_price < 0.1
            except Exception:
                prediction_correct = None

        if prediction_correct is True:
            status = 'verified_correct'
        elif prediction_correct is False:
            status = 'verified_incorrect'
        else:
            status = 'unverifiable'

        return {
            'symbol': symbol,
            'prediction': prediction,
            'prediction_date': prediction_date,
            'verification_date': current_date,
            'price_at_prediction': change['from_price'],
            'price_now': change['to_price'],
            'change': change['change'],
            'change_percent': change_pct,
            'high_in_period': change['high_in_period'],
            'low_in_period': change['low_in_period'],
            'trading_days': change['trading_days'],
            'prediction_correct': prediction_correct,
            'verification_status': status
        }

    def get_market_context(self, date: str) -> Dict:
        """
        获取某日的市场环境

        用于理解嘉宾发言时的市场状态

        Returns:
            {
                'date': '2025-01-15',
                'sp500': {'price': 5800, 'change_1m': 2.5},
                'nasdaq': {'price': 18500, 'change_1m': 3.2},
                'vix': 15.5,
                'treasury_10y': 4.5
            }
        """
        # 计算一个月前的日期
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        one_month_ago = (date_obj - timedelta(days=30)).strftime('%Y-%m-%d')

        context = {'date': date}

        # S&P 500
        sp500_change = self.get_price_change('^GSPC', one_month_ago, date)
        if sp500_change:
            context['sp500'] = {
                'price': sp500_change['to_price'],
                'change_1m': sp500_change['change_percent']
            }

        # NASDAQ
        nasdaq_change = self.get_price_change('^IXIC', one_month_ago, date)
        if nasdaq_change:
            context['nasdaq'] = {
                'price': nasdaq_change['to_price'],
                'change_1m': nasdaq_change['change_percent']
            }

        # VIX
        vix = self.get_price_history('^VIX', date, date)
        if vix:
            context['vix'] = vix[0]['close']

        # 10年期国债
        treasury = self.get_price_history('^TNX', date, date)
        if treasury:
            context['treasury_10y'] = treasury[0]['close']

        return context


# 便捷函数
_ds_singleton = None

def _get_ds():
    global _ds_singleton
    if _ds_singleton is None:
        _ds_singleton = DataSources()
    return _ds_singleton


def get_stock_price(symbol: str) -> Optional[Dict]:
    """快速获取股价"""
    return _get_ds().get_stock_price(symbol)


def get_price_change(symbol: str, from_date: str, to_date: str = None) -> Optional[Dict]:
    """快速计算价格变化"""
    return _get_ds().get_price_change(symbol, from_date, to_date)


def verify_prediction(symbol: str, prediction_date: str, prediction: str) -> Dict:
    """快速验证预测"""
    return _get_ds().verify_price_prediction(symbol, prediction_date, prediction)


# CLI 测试
if __name__ == "__main__":
    print("📊 数据源测试\n")

    ds = DataSources()

    # 测试获取股价
    print("1. 获取当前股价 (NVDA)")
    price = ds.get_stock_price('NVDA')
    if price:
        print(f"   {price['name']}: ${price['price']} ({price['change_percent']:+.2f}%)")
        print(f"   市值: ${price['market_cap']:,}" if price['market_cap'] else "")

    # 测试历史数据
    print("\n2. 获取历史数据 (NVDA, 最近5天)")
    history = ds.get_price_history('NVDA', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    if history:
        for h in history[-5:]:
            print(f"   {h['date']}: ${h['close']}")

    # 测试价格变化
    print("\n3. 计算价格变化 (NVDA, 过去30天)")
    change = ds.get_price_change('NVDA', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    if change:
        print(f"   从 ${change['from_price']} 到 ${change['to_price']}")
        print(f"   变化: {change['change_percent']:+.2f}%")

    # 测试财务数据
    print("\n4. 获取财务数据 (NVDA)")
    fin = ds.get_financials('NVDA')
    if fin:
        print(f"   P/E: {fin['pe_ratio']}")
        print(f"   市值: ${fin['market_cap']:,}" if fin['market_cap'] else "")
        print(f"   利润率: {fin['profit_margin']:.1%}" if fin['profit_margin'] else "")

    # 测试市场环境
    print("\n5. 获取市场环境")
    context = ds.get_market_context(datetime.now().strftime('%Y-%m-%d'))
    print(f"   S&P 500: {context.get('sp500', {}).get('price', 'N/A')}")
    print(f"   VIX: {context.get('vix', 'N/A')}")

    print("\n✅ 测试完成")
