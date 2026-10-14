import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Token do Bot do Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# IDs dos Canais do Discord (Obtidos clicando com botão direito no canal -> 'Copiar ID')
# Se OUTPUT_CHANNEL_ID for 0 ou None, o bot responde no mesmo canal onde o vídeo foi postado.
INPUT_CHANNEL_ID = int(os.getenv("INPUT_CHANNEL_ID", "0"))
OUTPUT_CHANNEL_ID = int(os.getenv("OUTPUT_CHANNEL_ID", "0"))

# Nome da Organização / Equipe para aparecer no topo do vídeo
TEAM_NAME = os.getenv("TEAM_NAME", "ESPORTS TEAM")

# Prefixo de comandos de texto (ex: !edit, !help)
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
