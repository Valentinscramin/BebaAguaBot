import discord
from discord import app_commands
from discord.ui import View, Button
import datetime
from database.db import Database
from services.hydration_service import HydrationService

db = Database()
service = HydrationService()

class ReminderView(View):
    def __init__(self, user_id: int, amount: float):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.amount = amount

    @discord.ui.button(label="✅ Bebi", style=discord.ButtonStyle.green)
    async def drank(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.update_consumption(self.user_id, self.amount)
        await interaction.response.send_message(f"💧 Ótimo! Você registrou {self.amount:.0f} ml.", ephemeral=True)

    @discord.ui.button(label="⏭️ Pular", style=discord.ButtonStyle.gray)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tudo bem, te lembrarei na próxima!", ephemeral=True)

    @discord.ui.button(label="🛑 Parar", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.stop_plan(self.user_id)
        user = db.get_user(self.user_id)
        
        # Resumo final
        consumed = user['consumed_ml']
        goal = user['daily_goal']
        percent = (consumed / goal * 100) if goal > 0 else 0
        
        await interaction.response.send_message(
            f"🛑 <@{self.user_id}>, você consumiu {consumed:.0f} ml de {goal:.0f} ml ({percent:.1f}%). "
            f"Ainda faltam {max(0, goal - consumed):.0f} ml para atingir sua meta de hoje."
        )

class HydrationCommands(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="hidratação", description="Comandos de hidratação")
        self.bot = bot

    @app_commands.command(name="configurar", description="Configura sua meta de hidratação")
    @app_commands.describe(
        peso_kg="Seu peso em kg",
        atividade="Nível de atividade física",
        intervalo_minutos="Intervalo entre lembretes (padrão 60)",
        horario_inicio="Horário de início (HH:MM)",
        horario_fim="Horário de término (HH:MM)"
    )
    @app_commands.choices(atividade=[
        app_commands.Choice(name="Sedentário", value="sedentário"),
        app_commands.Choice(name="Leve", value="leve"),
        app_commands.Choice(name="Moderado", value="moderado"),
        app_commands.Choice(name="Intenso", value="intenso"),
    ])
    async def hidratar(self, interaction: discord.Interaction, peso_kg: float, atividade: str, 
                        intervalo_minutos: int = 60, horario_inicio: str = None, horario_fim: str = None):
        
        user_id = interaction.user.id
        channel_id = interaction.channel_id
        
        # Temperatura simulada
        temp = service.get_current_temperature()
        goal = service.calculate_daily_goal(peso_kg, atividade, temp)
        
        # Gestão de horários
        now = datetime.datetime.now()
        if not horario_inicio:
            start_dt = now
        else:
            try:
                start_dt = datetime.datetime.strptime(horario_inicio, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
            except ValueError:
                await interaction.response.send_message("Formato de horário inválido. Use HH:MM", ephemeral=True)
                return

        if not horario_fim:
            end_dt = start_dt + datetime.timedelta(hours=16)
        else:
            try:
                end_dt = datetime.datetime.strptime(horario_fim, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
            except ValueError:
                await interaction.response.send_message("Formato de horário inválido. Use HH:MM", ephemeral=True)
                return

        if end_dt <= start_dt:
            end_dt += datetime.timedelta(days=1)

        # Cálculo de lembretes
        amount_per_reminder, num_reminders = service.calculate_reminder_amount(goal, start_dt, end_dt, intervalo_minutos)
        
        # Aviso de saúde
        health_warning = ""
        if goal >= 5000:
            health_warning = "\n\n⚠️ **Aviso:** A meta atingiu o limite máximo sugerido (5L). Se você tiver condições renais, cardíacas, estiver grávida ou seguir restrições de líquidos, procure orientação médica."

        # Salvar no banco
        db.save_user_plan(
            user_id, peso_kg, atividade, intervalo_minutos, 
            start_dt.strftime("%H:%M"), end_dt.strftime("%H:%M"), 
            goal, channel_id
        )

        embed = discord.Embed(title="💧 Plano de Hidratação Configurado!", color=discord.Color.blue())
        embed.add_field(name="Meta Diária", value=f"{goal:.0f} ml", inline=True)
        embed.add_field(name="Lembretes", value=f"{num_reminders} vezes", inline=True)
        embed.add_field(name="Quantidade/Lembrete", value=f"{amount_per_reminder:.0f} ml", inline=True)
        embed.add_field(name="Janela", value=f"{start_dt.strftime('%H:%M')} às {end_dt.strftime('%H:%M')}", inline=True)
        if health_warning:
            embed.description = health_warning

        await interaction.response.send_message(content=f"Olá <@{user_id}>!", embed=embed)

    @app_commands.command(name="status", description="Verifica seu progresso de hidratação")
    async def status(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user or not user['is_active']:
            await interaction.response.send_message("Você não tem um plano de hidratação ativo. Use `/hidratar` para começar!", ephemeral=True)
            return

        goal = user['daily_goal']
        consumed = user['consumed_ml']
        remaining = max(0, goal - consumed)
        percent = (consumed / goal * 100) if goal > 0 else 0
        
        # Próximo lembrete (estimativa baseada no intervalo)
        # Aqui assumimos que o bot está rodando e o loop de tarefas cuida disso.
        
        embed = discord.Embed(title="📊 Status de Hidratação", color=discord.Color.blue())
        embed.add_field(name="Meta Total", value=f"{goal:.0f} ml", inline=True)
        embed.add_field(name="Consumido", value=f"{consumed:.0f} ml", inline=True)
        embed.add_field(name="Restante", value=f"{remaining:.0f} ml", inline=True)
        embed.add_field(name="Progresso", value=f"{percent:.1f}%", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="parar", description="Interrompe os lembretes de hidratação")
    async def parar(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user = db.get_user(user_id)
        if not user or not user['is_active']:
            await interaction.response.send_message("Você não tem um plano ativo.", ephemeral=True)
            return

        db.stop_plan(user_id)
        
        consumed = user['consumed_ml']
        goal = user['daily_goal']
        percent = (consumed / goal * 100) if goal > 0 else 0
        
        await interaction.response.send_message(
            f"🛑 <@{user_id}>, você consumiu {consumed:.0f} ml de {goal:.0f} ml ({percent:.1f}%). "
            f"Ainda faltam {max(0, goal - consumed):.0f} ml para atingir sua meta de hoje."
        )
