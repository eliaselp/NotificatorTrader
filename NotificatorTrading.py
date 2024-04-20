import pickle
import os
from tradingview_ta import TA_Handler, Interval, Exchange
import time

class SwingTradingBot:
    def __init__(self, symbol, screener, exchange, interval):
        self.handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=interval
        )
        self.last_operation = None
        self.last_price = None

    def get_current_price(self):
        analysis = self.handler.get_analysis()
        return analysis.indicators['close']

    def get_analysis(self):
        return self.handler.get_analysis()

    def trade_decision(self, analysis):
        current_price = self.get_current_price()
        summary = analysis.summary
        indicators = analysis.indicators
        recommendation = summary['RECOMMENDATION']
        
        # Si hay una posición abierta, decidir si mantenerla o cerrarla
        if self.last_operation:
            if self.should_close_position(recommendation):
                self.close_position(current_price)
            else:
                print(f"Manteniendo la posición {self.last_operation} a {current_price}.")
        else:
            if recommendation == 'STRONG_BUY':
                self.open_long_position(indicators, current_price)
            elif recommendation == 'STRONG_SELL':
                self.open_short_position(indicators, current_price)

    def should_close_position(self, recommendation):
        # Lógica para decidir si cerrar la posición
        # Por ejemplo, cerrar en recomendaciones neutrales o contrarias
        return recommendation in ['SELL', 'NEUTRAL', 'BUY'] if self.last_operation == 'LONG' \
            else recommendation in ['BUY', 'NEUTRAL', 'SELL']

    def open_long_position(self, indicators, current_price):
        print(f"Señal de COMPRA fuerte detectada a {current_price}, abriendo posición en largo.")
        self.print_indicators(indicators)
        self.last_operation = 'LONG'
        self.last_price = current_price
        self.save_state()

    def open_short_position(self, indicators, current_price):
        print(f"Señal de VENTA fuerte detectada a {current_price}, abriendo posición en corto.")
        self.print_indicators(indicators)
        self.last_operation = 'SHORT'
        self.last_price = current_price
        self.save_state()

    def close_position(self, current_price):
        print(f"Señal de {self.last_operation} cerrada a {current_price}.")
        self.last_operation = None
        self.last_price = None
        self.save_state()

    def print_indicators(self, indicators):
        print("Detalles de los indicadores:")
        for key, value in indicators.items():
            print(f"{key}: {value}")

    def save_state(self):
        with open('bot_state.pkl', 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load_state():
        if os.path.exists('bot_state.pkl'):
            with open('bot_state.pkl', 'rb') as file:
                return pickle.load(file)
        else:
            return None

def run_bot():
    # Configuración del bot
    symbol = "BTCUSDT"
    screener = "crypto"
    exchange = "BINANCE"
    interval = Interval.INTERVAL_4_HOURS

    # Intentar recuperar el estado del bot
    bot = SwingTradingBot.load_state()
    if bot is None:
        bot = SwingTradingBot(symbol, screener, exchange, interval)

    # Iniciar el bot
    while True:
        analysis = bot.get_analysis()
        bot.trade_decision(analysis)
        time.sleep(60 * 60 * 4)  # Espera de 4 horas entre cada análisis

if __name__ == "__main__":
    run_bot()
