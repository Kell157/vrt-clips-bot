FROM python:3.11-slim

# Instala FFmpeg e dependências de fontes
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-freefont-ttf \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Executa o bot sem buffer
CMD ["python", "-u", "bot/discord_bot.py"]
