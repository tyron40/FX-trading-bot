import time
from livetrading.SMALive import SMALive
import configparser

def run_trader(instrument="EUR_USD", granularity="1m", units=1907, smas=5, smal=15, stop_loss=-5):
    """Run the trading bot with automatic reconnection on failure."""
    
    while True:
        try:
            # Load config
            cfg = configparser.ConfigParser()
            cfg.read('oanda.cfg')
            
            print(f"\nStarting trading session with:")
            print(f"Instrument: {instrument}")
            print(f"Granularity: {granularity}")
            print(f"Units: {units}")
            print(f"SMAS: {smas}")
            print(f"SMAL: {smal}")
            print(f"Stop Loss: ${stop_loss}")
            
            # Create and start trader
            trader = SMALive(
                cfg=cfg,
                instrument=instrument,
                bar_length=granularity,
                smas=smas,
                smal=smal,
                units=units,
                stop_loss=stop_loss
            )
            
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            print("Attempting to reconnect in 5 seconds...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    run_trader()
