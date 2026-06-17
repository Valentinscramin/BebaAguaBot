import datetime
from typing import Tuple, Optional

class HydrationService:
    @staticmethod
    def calculate_daily_goal(weight_kg: float, activity: str, temperature: float = 25.0) -> float:
        # Meta base: 35 ml * peso_kg
        goal = 35 * weight_kg
        
        # Adições por atividade
        activity_bonuses = {
            "sedentário": 0,
            "leve": 250,
            "moderado": 500,
            "intenso": 750
        }
        goal += activity_bonuses.get(activity.lower(), 0)
        
        # Temperatura acima de 28°C: +10%
        if temperature > 28:
            goal *= 1.1
            
        # Limite máximo de 5 litros
        return min(goal, 5000.0)

    @staticmethod
    def calculate_reminder_amount(daily_goal: float, start_time: datetime.datetime, end_time: datetime.datetime, interval_minutes: int) -> Tuple[float, int]:
        # Calcula a janela de tempo em minutos
        delta = end_time - start_time
        total_minutes = delta.total_seconds() / 60
        
        # Número de lembretes
        num_reminders = int(total_minutes // interval_minutes)
        if num_reminders == 0:
            num_reminders = 1
            
        amount_per_reminder = daily_goal / num_reminders
        return amount_per_reminder, num_reminders

    @staticmethod
    def get_current_temperature(city: str = "Sao Paulo") -> float:
        # Em um cenário real, usaria uma API de clima. 
        # Para este bot, simularemos ou usaremos um valor fixo se não houver API key.
        # Retornaremos 25.0 como padrão.
        return 25.0
