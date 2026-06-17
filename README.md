# 💧 BotDagua - Guia de Instalação e Execução

Este bot ajuda usuários do Discord a manterem uma rotina de hidratação saudável, calculando metas diárias e enviando lembretes periódicos.

## 🚀 Requisitos

- Python 3.10 ou superior
- Uma conta no [Discord Developer Portal](https://discord.com/developers/applications)
- `pip` (instalador de pacotes do Python)

## 🛠️ Instalação

1. **Clonar o repositório** (ou baixar a pasta):
   ```bash
   cd BotDagua
   ```

2. **Criar um ambiente virtual (Recomendado)**:
   ```bash
   python -m venv venv
   # No Windows:
   .\venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependências**:
   ```bash
   pip install discord.py python-dotenv
   ```

4. **Configurar o Token**:
   - Abra o arquivo `.env` na raiz do projeto.
   - Substitua `seu_token_aqui_123456789` pelo token do seu bot obtido no Discord Developer Portal.

## 🏃 Execução

Para iniciar o bot, execute:
```bash
python main.py
```

## 📖 Como usar os comandos

O bot utiliza **Slash Commands** (comandos de barra). Digite `/` no Discord para ver as opções:

- `/hidratação configurar`: Define seu peso, nível de atividade e horários. O bot calculará sua meta e começará a enviar lembretes.
- `/hidratação status`: Mostra quanto você já bebeu e quanto falta para a meta.
- `/hidratação parar`: Interrompe os lembretes e mostra um resumo do seu dia.

## ⚙️ Detalhes Técnicos

- **Persistência**: SQLite (`hydration_bot.db`)
- **Lógica de Meta**: 
  - Base: $35\text{ml} \times \text{peso}$
  - Bônus de atividade: Leve (+250ml), Moderado (+500ml), Intenso (+750ml)
  - Calor: +10% se temperatura > 28°C
  - Limite: Máximo 5L/dia
- **Lembretes**: Calculados dividindo a meta total pelo número de intervalos na janela de tempo definida.
