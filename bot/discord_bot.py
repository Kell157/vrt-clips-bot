import os
import re
import asyncio
from pathlib import Path
import discord
from discord.ext import commands
import sys

# Força UTF-8 para stdout e stderr no Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import functools
print = functools.partial(print, flush=True)

# Adiciona o diretório raiz ao sys.path para importar config e core
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from core.video_editor import render_vertical_gameplay, generate_hook_and_comment

# Lista dos campeões do LoL para auto-detecção em mensagens
LOL_CHAMPIONS = [
    "Aatrox", "Ahri", "Akali", "Akshan", "Alistar", "Ambessa", "Amumu", "Anivia", "Annie", "Aphelios",
    "Ashe", "Aurelion Sol", "Aurora", "Azir", "Bard", "Bel'Veth", "Blitzcrank", "Brand", "Braum", "Briar",
    "Caitlyn", "Camille", "Cassiopeia", "Cho'Gath", "Corki", "Darius", "Diana", "Dr. Mundo", "Draven",
    "Ekko", "Elise", "Evelynn", "Ezreal", "Fiddlesticks", "Fiora", "Fizz", "Galio", "Gangplank", "Garen",
    "Gnar", "Gragas", "Graves", "Gwen", "Hecarim", "Heimerdinger", "Hwei", "Illaoi", "Irelia", "Ivern",
    "Janna", "Jarvan IV", "Jax", "Jayce", "Jhin", "Jinx", "K'Sante", "Kai'Sa", "Kalista", "Karma",
    "Karthus", "Kassadin", "Katarina", "Kayle", "Kayn", "Kennen", "Kha'Zix", "Kindred", "Kled", "Kog'Maw",
    "LeBlanc", "Lee Sin", "Leona", "Lillia", "Lissandra", "Lucian", "Lulu", "Lux", "Malphite", "Malzahar",
    "Maokai", "Master Yi", "Milio", "Miss Fortune", "Mordekaiser", "Morgana", "Naafiri", "Nami", "Nasus",
    "Nautilus", "Neeko", "Nidalee", "Nilah", "Nocturne", "Nunu", "Olaf", "Orianna", "Ornn", "Pantheon",
    "Poppy", "Pyke", "Qiyana", "Quinn", "Rakan", "Rammus", "Rek'Sai", "Rell", "Renata Glasc", "Renekton",
    "Rengar", "Riven", "Rumble", "Ryze", "Samira", "Sejuani", "Senna", "Seraphine", "Sett", "Shaco",
    "Shen", "Shyvana", "Singed", "Sion", "Sivir", "Skarner", "Smolder", "Sona", "Soraka", "Swain",
    "Sylas", "Syndra", "Tahm Kench", "Taliyah", "Talon", "Taric", "Teemo", "Thresh", "Tristana", "Trundle",
    "Tryndamere", "Twisted Fate", "Twitch", "Udyr", "Urgot", "Varus", "Vayne", "Veigar", "Vel'Koz", "Vex",
    "Vi", "Viego", "Viktor", "Vladimir", "Volibear", "Warwick", "Wukong", "Xayah", "Xerath", "Xin Zhao",
    "Yasuo", "Yone", "Yorick", "Yuumi", "Zac", "Zed", "Zeri", "Ziggs", "Zilean", "Zoe", "Zyra"
]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

def detect_champion(text: str) -> str:
    """Tenta identificar o campeão citado na legenda da mensagem."""
    if not text:
        return None
    text_lower = text.lower()
    for champ in LOL_CHAMPIONS:
        # Busca como palavra isolada
        pattern = r"\b" + re.escape(champ.lower()) + r"\b"
        if re.search(pattern, text_lower):
            return champ
    return None

def extract_details(text: str):
    """Extrai detalhes como '1v3', '100 hp', 'outplay' da mensagem."""
    if not text:
        return "100 DE HP"
    match = re.search(r"\b(1v\d|\d+v\d|\d+\s?hp|\d+%\s?hp|sem flash|outplay|solo kill)\b", text, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return "100 DE HP"

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado com sucesso como: {bot.user.name} (ID: {bot.user.id})")
    print(f"🎯 Monitorando canal de entrada: {config.INPUT_CHANNEL_ID or 'Todos os canais com anexo'}")
    print(f"🚀 Organização: {config.TEAM_NAME}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="gameplays para Shorts/Reels"))

@bot.event
async def on_message(message: discord.Message):
    # Ignora mensagens do próprio bot
    if message.author.bot:
        return
    
    # Processa comandos caso a mensagem comece com o prefixo
    await bot.process_commands(message)

    # Verifica se deve filtrar por canal específico
    if config.INPUT_CHANNEL_ID != 0 and message.channel.id != config.INPUT_CHANNEL_ID:
        return

    # Procura por vídeos anexados
    video_attachments = [
        att for att in message.attachments 
        if att.filename.lower().endswith(('.mp4', '.mov', '.webm', '.mkv'))
    ]

    if not video_attachments:
        return

    for att in video_attachments:
        await process_attachment(message, att)

async def process_attachment(
    message: discord.Message, 
    attachment: discord.Attachment,
    custom_champion: str = None,
    custom_detail: str = None
):
    """Baixa o clipe, processa o vídeo e envia de volta ao Discord."""
    try:
        await message.add_reaction("⏳")
    except Exception as e:
        print(f"Aviso: Não foi possível adicionar reação de ampulheta (permissão): {e}")

    status_msg = None
    try:
        status_msg = await message.reply("🎬 **Gameplay recebida!** Iniciando a edição viral com o roteiro de retenção...")
    except Exception as e:
        print(f"Aviso: Não foi possível responder com status_msg: {e}")
        try:
            status_msg = await message.channel.send(f"🎬 {message.author.mention}, iniciando a edição da sua gameplay...")
        except Exception:
            pass
    
    inputs_dir = BASE_DIR / "inputs"
    outputs_dir = BASE_DIR / "output"
    clean_name = Path(attachment.filename).stem
    input_path = inputs_dir / f"{message.id}_{attachment.filename}"
    output_path = outputs_dir / f"final_{message.id}_{clean_name}.mp4"
    
    # 1. Download do vídeo
    print(f"Baixando vídeo: {attachment.filename} ({attachment.size} bytes)")
    await attachment.save(input_path)
    print(f"Vídeo baixado com sucesso em: {input_path}")
    
    # 2. Identificação de Campeão e Situação pela mensagem ou parâmetros
    caption = message.content
    champion = custom_champion or detect_champion(caption)
    detail = custom_detail or extract_details(caption)
    
    # 3. Renderização em background (não bloqueia o bot)
    try:
        result = await asyncio.to_thread(
            render_vertical_gameplay,
            input_video_path=str(input_path),
            output_video_path=str(output_path),
            champion=champion,
            detail=detail,
            badge_text=config.TEAM_NAME
        )
        
        # 4. Envio do vídeo para o canal de destino ou mesmo canal
        target_channel = message.channel
        if config.OUTPUT_CHANNEL_ID != 0:
            dest = bot.get_channel(config.OUTPUT_CHANNEL_ID)
            if dest:
                target_channel = dest
                
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        embed = discord.Embed(
            title="🔥 Vídeo Editado Pronto para Publicação!",
            color=0xFEE715,
            description="Clipe renderizado no formato vertical (9:16) seguindo a fórmula de alta retenção."
        )
        embed.add_field(name="🎯 Gancho Utilizado", value=f"**{result['hook_text']}**", inline=False)
        embed.add_field(name="💬 Pergunta de Retenção", value=f"*{result['comment_text']}*", inline=False)
        embed.add_field(name="👤 Jogador", value=message.author.mention, inline=True)
        embed.add_field(name="⏱️ Duração", value=f"{result['duration']:.1f}s", inline=True)
        embed.add_field(
            name="📋 Sugestão para o Marketing (Legenda/Tags)",
            value=f"```text\n{result['hook_text']}\n\nJogada insana do @{message.author.name}!\n\n#LeagueOfLegends #LoLClips #LoLBrasil #Esports #{champion or 'LoL'}\n```",
            inline=False
        )
        
        if file_size_mb <= 24:
            file_to_send = discord.File(str(output_path), filename=f"short_{clean_name}.mp4")
            await target_channel.send(content=f"🚀 {message.author.mention}, seu vídeo foi editado!", embed=embed, file=file_to_send)
        else:
            # Caso ultrapasse o limite de upload do plano do Discord
            embed.set_footer(text=f"⚠️ Vídeo com {file_size_mb:.1f}MB salvo localmente no servidor da equipe.")
            await target_channel.send(content=f"🚀 {message.author.mention}, seu vídeo foi editado!", embed=embed)
            
        await message.remove_reaction("⏳", bot.user)
        await message.add_reaction("✅")
        await status_msg.delete()
        
    except Exception as e:
        await message.remove_reaction("⏳", bot.user)
        await message.add_reaction("❌")
        await status_msg.edit(content=f"❌ **Erro na renderização:** `{str(e)}`")
        print(f"Erro ao processar clipe: {e}")

@bot.command(name="edit")
async def cmd_edit(ctx, *, args: str = ""):
    """Edita um vídeo antigo respondendo a ele com !edit ou colando o link."""
    target_message = None
    
    # Caso 1: Usuário usou responder (reply) na mensagem antiga
    if ctx.message.reference and ctx.message.reference.message_id:
        try:
            target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception:
            pass
            
    # Caso 2: O comando foi enviado com um vídeo anexado
    elif ctx.message.attachments:
        target_message = ctx.message
        
    # Caso 3: O usuário colou o link da mensagem
    if not target_message and args:
        match = re.search(r"channels/\d+/(\d+)/(\d+)", args)
        if match:
            channel_id, msg_id = int(match.group(1)), int(match.group(2))
            ch = bot.get_channel(channel_id)
            if ch:
                try:
                    target_message = await ch.fetch_message(msg_id)
                except Exception:
                    pass

    if not target_message:
        await ctx.reply("💡 **Como editar um vídeo antigo:**\n1. Clique em **Responder** na mensagem antiga com o vídeo e digite: `!edit Aphelios 1v3`\n2. Ou simplesmente reaja na mensagem do vídeo com o emoji 🎬")
        return

    video_attachments = [
        att for att in target_message.attachments 
        if att.filename.lower().endswith(('.mp4', '.mov', '.webm', '.mkv'))
    ]

    if not video_attachments:
        await ctx.reply("⚠️ Não encontrei nenhum anexo de vídeo (.mp4, .mov, etc.) na mensagem selecionada.")
        return

    custom_champ = detect_champion(args)
    custom_det = extract_details(args)

    for att in video_attachments:
        await process_attachment(target_message, att, custom_champion=custom_champ, custom_detail=custom_det)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """Permite editar qualquer vídeo antigo apenas adicionando a reação 🎬 na mensagem."""
    if payload.user_id == bot.user.id:
        return
        
    if str(payload.emoji) in ["🎬", "✂️"]:
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            msg = await channel.fetch_message(payload.message_id)
            video_attachments = [
                att for att in msg.attachments 
                if att.filename.lower().endswith(('.mp4', '.mov', '.webm', '.mkv'))
            ]
            if video_attachments:
                for att in video_attachments:
                    await process_attachment(msg, att)
        except Exception as e:
            import traceback
            print(f"Erro ao processar reação: {e}")
            traceback.print_exc()

@bot.command(name="status")
async def bot_status(ctx):
    """Verifica se o bot de edição está operando normalmente."""
    await ctx.reply(f"🟢 **Bot de Edição de Vídeos Ativo!**\nOrganização: `{config.TEAM_NAME}`\nCanal de Entrada: `<#{config.INPUT_CHANNEL_ID}>`\n\n📌 *Dica:* Para editar vídeos antigos, basta reagir neles com 🎬 ou responder com `!edit [Campeão]`!")

if __name__ == "__main__":
    if not config.DISCORD_TOKEN or config.DISCORD_TOKEN == "SEU_TOKEN_AQUI":
        print("❌ AVISO: O DISCORD_TOKEN não foi configurado no arquivo .env!")
        print("👉 Abra o arquivo .env e insira o token do bot gerado no Discord Developer Portal.")
    else:
        bot.run(config.DISCORD_TOKEN)
