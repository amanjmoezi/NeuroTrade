"""
Main Entry Point - CLI Mode
Modular version with clean architecture
"""
import asyncio
import json
import argparse
from src.core.config import Config
from src.trading.system import TradingSystem


async def main_async():
    """Main async function for CLI mode"""
    parser = argparse.ArgumentParser(description='ICT Trading System v3.0')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    args = parser.parse_args()
    
    config = Config()
    system = TradingSystem(config)
    
    try:
        result = await system.analyze(args.symbol)
        
        print("\n" + "="*80)
        print("🤖 ICT TRADING SIGNAL")
        print("="*80)
        print(json.dumps(result['signal'], indent=2, ensure_ascii=False))
        print("="*80 + "\n")
        
    finally:
        await system.cleanup()


def main():
    """Main entry point"""
    print("🚀 ICT Trading System v3.0 Started (CLI Mode)")
    print("="*80)
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
