import requests
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class CurrencyConverter:
    def __init__(self):
        self.api_key = os.getenv('EXCHANGERATE_API_KEY')
        if not self.api_key or self.api_key == 'your-exchangerate-api-key-here':
            raise ValueError("EXCHANGERATE_API_KEY não configurada corretamente no arquivo .env")
        self.base_url = 'https://v6.exchangerate-api.com/v6'
        
    @lru_cache(maxsize=32)  # Cache para evitar chamadas repetidas
    def get_rate(self, from_currency: str, to_currency: str = 'BRL') -> float:
        """Obtém a taxa de câmbio atual entre duas moedas."""
        try:
            url = f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data['conversion_rate']
        except requests.RequestException as e:
            print(f"Erro ao obter taxa de câmbio: {e}")
            print(f"URL tentada: {url}")  # Log para debug
            return None
            
    def convert(self, amount: float, from_currency: str, to_currency: str = 'BRL') -> float:
        """Converte um valor de uma moeda para outra."""
        if from_currency == to_currency:
            return amount
            
        rate = self.get_rate(from_currency, to_currency)
        if rate is None:
            return amount  # Retorna o valor original se a conversão falhar
            
        return amount * rate

# Instância global para ser usada em toda a aplicação
converter = CurrencyConverter() 