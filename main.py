import discord
from discord import app_commands
import asyncio
import datetime
from dotenv import load_dotenv
import os
from database.db import Database
from services.hydration_service import HydrationService
from commands.hydration import ReminderView

class BotDagua(discord.Client):
    def __init__(self, token):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        
        self.token = token
        self.tree = app_commands.CommandTree(self)
        self.db = Database()
        self.service = HydrationService()

    async def setup_hook(self):
        # Importar e adicionar comandos
        from commands.hydration import HydrationCommands
        hydration_cmds = HydrationCommands(self)
        self.tree.add_command(hydration_cmds)
        
        # Sincronizar comandos slash
        await self.tree.sync()
        
        # Iniciar loop de lembretes
        self.loop.create_task(self.reminder_loop())

    async def reminder_loop(self):
        while True:
            now = datetime.datetime.now()
            active_plans = self.db.get_active_plans()
            
            for plan in active_plans:
                user_id = plan['user_id']
                channel_id = plan['channel_id']
                interval = plan['interval_minutes']
                start_time_str = plan['start_time']
                end_time_str = plan['end_time']
                goal = plan['daily_goal']
                
                # Verificar se está dentro da janela de tempo
                current_time_str = now.strftime("%H:%M")
                if not (start_time_str <= current_time_str <= end_time_str):
                    continue
                
                # Verificar se já passou o intervalo desde o último lembrete
                last_reminder = plan['last_reminder_time']
                should_remind = False
                
                if last_reminder is None:
                    should_remind = True
                else:
                    last_dt = datetime.datetime.strptime(last_reminder, "%Y-%m-%d %H:%M:%S")
                    if (now - last_dt).total_seconds() >= interval * 60:
                        should_remind = True
                
                if should_remind:
                    # Calcular quantidade por lembrete
                    start_dt = datetime.datetime.strptime(start_time_str, "%H:%M").replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    end_dt = datetime.datetime.strptime(end_time_str, "%H:%M").replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    if end_dt <= start_dt:
                        end_dt += datetime.timedelta(days=1)
                        
                    amount, _ = self.service.calculate_reminder_amount(goal, start_dt, end_dt, interval)
                    
                    # Enviar mensagem
                    channel = self.get_channel(channel_id)
                    if channel:
                        view = ReminderView(user_id, amount)
                        await channel.send(f"💧 <@{user_id}>, hora de beber {amount:.0f} ml de água!", view=view)
                        
                        # Atualizar último lembrete
                        self.db.update_last_reminder(user_id, now.strftime("%Y-%m-%d %H:%M:%S"))
            
            await asyncio.sleep(60) # Verificar a cada minuto

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if not TOKEN:
        print("Erro: DISCORD_TOKEN não encontrado no arquivo .env")
    else:
        client = BotDagua(TOKEN)
        try:
            client.run(TOKEN)
        except discord.errors.LoginFailure:
            print("Erro: Token do Discord inválido. Verifique seu arquivo .env")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
