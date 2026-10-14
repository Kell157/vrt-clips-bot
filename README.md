# 🎮 League of Legends - Bot de Edição Automatizada de Clipes

Sistema automatizado para equipes de esports e criadores de conteúdo de LoL. O bot monitora um canal específico no Discord, baixa os clipes de gameplay enviados pelos jogadores e renderiza automaticamente um vídeo vertical (9:16) seguindo a fórmula viral de alta retenção (TikTok, Reels e YouTube Shorts).

---

## ⚡ Roteiro de Edição Implementado

1. **Gancho Visual e Texto (0s a 3.5s)**:
   - Texto em caixa alta com fonte grossa (Impact), amarelo e branco com borda preta.
   - Efeito sonoro sintético de impacto (**Whoosh / Bass Drop**) no segundo 00:00.
   - Badge com a organização/equipe no topo.
2. **Tensão / Build-up (3s a 8s)**:
   - Zoom cinematográfico gradual (100% até 115%) focando na ação principal da gameplay.
3. **Clímax e Gameplay**:
   - Centralização nítida da gameplay horizontal em formato vertical com fundo desfocado (*gaussian blur*).
4. **Desfecho e Loop Infinito (Últimos 3.5s)**:
   - Pergunta provocativa para forçar comentários e engajamento (*"Isso foi cálculo ou pura sorte?"*).
   - Sem despedidas; corte milimétrico que reinicia o vídeo suavemente.

---

## 🚀 Como Colocar para Rodar

### 1. Criar o Bot no Discord Developer Portal (Leva 2 minutos)
1. Acesse: [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Clique em **"New Application"** e dê um nome (ex: `LoL Clips Editor`).
3. Vá no menu lateral em **Bot**:
   - Clique em **"Reset Token"** e copie o seu **Token**.
   - Role até a seção **"Privileged Gateway Intents"** e ative:
     - ✅ **Message Content Intent** (essencial para o bot ler os anexos de vídeo).
4. Vá em **OAuth2 -> URL Generator**:
   - Em *Scopes*, marque: `bot`.
   - Em *Bot Permissions*, marque:
     - `Send Messages`
     - `Attach Files`
     - `Read Message History`
     - `Add Reactions`
   - Copie o link gerado no final e cole no seu navegador para convidar o bot para o servidor da sua equipe.

---

### 2. Configurar o Arquivo `.env`
No diretório do projeto, crie ou edite o arquivo `.env`:
```env
DISCORD_TOKEN=seu_token_aqui
INPUT_CHANNEL_ID=id_do_canal_de_envios
OUTPUT_CHANNEL_ID=id_do_canal_do_marketing
TEAM_NAME=NOME DA SUA EQUIPE
```

> **Dica para pegar os IDs dos canais:** No Discord, ative o Modo Desenvolvedor (*Configurações de Usuário -> Avançado -> Modo Desenvolvedor*). Depois, basta clicar com o botão direito no canal e selecionar **"Copiar ID"**.

---

### 3. Iniciar o Bot
Execute no terminal:
```bash
python bot/discord_bot.py
```

Assim que um jogador subir um arquivo de vídeo (`.mp4`, `.mov`, etc.) no canal configurado, o bot reagirá com ⏳, processará a edição e postará o resultado final pronto para o time de marketing publicar!
