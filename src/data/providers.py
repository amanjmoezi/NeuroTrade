"""
Data Providers - Binance REST API
"""
import aiohttp
import pandas as pd
from src.core.config import Config


class BinanceDataProvider:
    """Fetch Data from Binance REST API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.timeframe_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "2h": "2h", "4h": "4h",
            "6h": "6h", "8h": "8h", "12h": "12h", "1d": "1d",
            "3d": "3d", "1w": "1w", "1M": "1M"
        }
    
    async def _get_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.http_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Fetch OHLCV data from Binance"""
        try:
            session = await self._get_session()
            interval = self.timeframe_map.get(timeframe, "1h")
            
            url = f"{self.config.binance_api}/api/v3/klines"
            params = {"symbol": symbol, "interval": interval, "limit": limit}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"Binance API Error {response.status} for {symbol} {interval}: {error_text[:200]}"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                
                data = await response.json()
                if not data or len(data) == 0:
                    error_msg = f"No data returned for {symbol} {interval}"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].reset_index(drop=True)
                
        except aiohttp.ClientError as e:
            error_msg = f"Network error for {symbol} {timeframe}: {type(e).__name__} - {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error fetching OHLCV for {symbol} {timeframe}: {type(e).__name__} - {str(e) or 'Unknown error'}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            session = await self._get_session()
            url = f"{self.config.binance_api}/api/v3/ticker/price"
            params = {"symbol": symbol}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"Binance API Error {response.status} for price {symbol}: {error_text[:200]}"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                
                data = await response.json()
                return float(data['price'])
        except Exception as e:
            error_msg = f"Error fetching price for {symbol}: {type(e).__name__} - {str(e) or 'Unknown error'}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    async def get_funding_rate(self, symbol: str) -> float:
        """Get funding rate for futures"""
        try:
            session = await self._get_session()
            url = f"{self.config.binance_futures_api}/fapi/v1/fundingRate"
            params = {"symbol": symbol, "limit": 1}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    print(f"⚠️ Funding rate not available for {symbol} (status {response.status})")
                    return 0.0
                
                data = await response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return float(data[0]['fundingRate'])
                return 0.0
        except Exception as e:
            print(f"⚠️ Error fetching funding rate for {symbol}: {type(e).__name__}")
            return 0.0
    
    async def get_open_interest(self, symbol: str) -> float:
        """Get open interest for futures"""
        try:
            session = await self._get_session()
            url = f"{self.config.binance_futures_api}/fapi/v1/openInterest"
            params = {"symbol": symbol}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    print(f"⚠️ Open interest not available for {symbol} (status {response.status})")
                    return 0.0
                
                data = await response.json()
                return float(data['openInterest'])
        except Exception as e:
            print(f"⚠️ Error fetching open interest for {symbol}: {type(e).__name__}")
            return 0.0
