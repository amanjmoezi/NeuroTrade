"""
Chart Generator - Create trading charts
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from io import BytesIO
from typing import Dict
import logging
import tempfile
import os


class ChartGenerator:
    """Generate trading charts"""
    
    def generate_chart(self, market_data: Dict, signal: Dict, symbol: str) -> str:
        """Generate chart and save to temporary file, returns file path"""
        try:
            # Create chart using existing method
            chart_buffer = self.create_price_chart(market_data, signal)
            
            if chart_buffer is None:
                raise Exception("Failed to create chart buffer")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix=f'chart_{symbol}_')
            temp_file.write(chart_buffer.getvalue())
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logging.error(f"Error generating chart file: {e}")
            raise
    
    @staticmethod
    def create_price_chart(market_data: Dict, signal: Dict) -> BytesIO:
        """Create price chart with signals"""
        try:
            ohlcv = market_data['market_data']['ohlcv'][-100:]
            df = pd.DataFrame(ohlcv)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
            ax1.plot(df['timestamp'], df['close'], label='Price', color='#2962FF', linewidth=2)
            
            # FVG zones
            for fvg in market_data['zones']['fvgs'][-3:]:
                if not fvg['mitigated']:
                    color = 'green' if fvg['type'] == 'BULL' else 'red'
                    ax1.axhspan(fvg['bottom'], fvg['top'], alpha=0.2, color=color)
            
            # Entry zone
            if 'position' in signal and 'entry_zone' in signal['position']:
                entry_price = signal['position']['entry_zone'].get('optimal', 0)
                if entry_price > 0:
                    ax1.axhline(y=entry_price, color='blue', linestyle='--', label=f'Entry: ${entry_price:,.2f}')
            
            # Take profit targets
            if 'position' in signal and 'take_profit' in signal['position']:
                tp_data = signal['position']['take_profit']
                if isinstance(tp_data, list):
                    for i, tp_obj in enumerate(tp_data[:3], 1):
                        if 'price' in tp_obj:
                            ax1.axhline(y=tp_obj['price'], color='green', linestyle=':', 
                                      label=f'TP{i}: ${tp_obj["price"]:,.2f}')
                elif isinstance(tp_data, dict):
                    tp_keys = ['primary', 'secondary']
                    for i, key in enumerate(tp_keys, 1):
                        if key in tp_data and tp_data[key] > 0:
                            ax1.axhline(y=tp_data[key], color='green', linestyle=':', 
                                      label=f'TP{i}: ${tp_data[key]:,.2f}')
            
            # Stop loss
            if 'position' in signal and 'stop_loss' in signal['position']:
                sl_price = signal['position']['stop_loss'].get('price', 0)
                if sl_price > 0:
                    ax1.axhline(y=sl_price, color='red', linestyle=':', label=f'SL: ${sl_price:,.2f}')
            
            ax1.set_title(f"{market_data['market_data']['symbol']} - ICT Analysis", fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price (USDT)', fontsize=12)
            ax1.legend(loc='upper left', fontsize=9)
            ax1.grid(True, alpha=0.3)
            
            # Volume
            colors = ['green' if df['close'].iloc[i] >= df['open'].iloc[i] else 'red' for i in range(len(df))]
            ax2.bar(df['timestamp'], df['volume'], color=colors, alpha=0.6)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.set_xlabel('Time', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            logging.error(f"Error creating chart: {e}")
            return None
