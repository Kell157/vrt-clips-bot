"""
Módulo de Edição Automática de Vídeos de LoL para Shorts/Reels/TikTok
Baseado no roteiro de alta retenção:
1. Gancho Visual e Texto (0s a 3s)
2. Tensão / Build-up (3s a 8s) com zoom gradual na ação
3. Clímax / A Jogada (8s+)
4. Desfecho com Loop Infinito e pergunta de engajamento (Últimos 3 a 5s)
"""

import os
import random
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Caminhos padrão
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"
FONTS_DIR = ASSETS_DIR / "fonts"
BRANDING_DIR = ASSETS_DIR / "branding"
OUTPUT_DIR = BASE_DIR / "output"

# Templates de Gancho (0s a 3s)
HOOK_TEMPLATES = {
    "provocacao": [
        "NUNCA SUBESTIME UM {champion} COM {detail}",
        "ELE ACHOU QUE IA SAIR VIVO DESSA...",
        "O QUE ESSE {champion} FEZ DEVERIA SER CRIME!",
        "ACHOU QUE ESTAVA SEGURO DEBAIXO DA TORRE?",
        "NÃO FAÇA ISSO CONTRA UM {champion}!"
    ],
    "desafio": [
        "O TIME ACHOU QUE A PARTIDA TAVA PERDIDA...",
        "1% DE VIDA, 99% DE FÉ!",
        "QUANDO SEU {champion} DECIDE CARREGAR O JOGO",
        "ERA PRA SER UM GANK COMUM, MAS...",
        "NENHUM HUMANO JOGA ASSIM COM {champion}"
    ],
    "mecanica": [
        "POR ISSO VOCÊ NUNCA DEVE AGRUPAR CONTRA {champion}",
        "A MECÂNICA MAIS LIMPA QUE VOCÊ VAI VER HOJE",
        "FLASH CALCULADO OU PURA SORTE?",
        "COMO ACABAR COM A TEAMFIGHT EM 3 SEGUNDOS"
    ]
}

# Perguntas de Encerramento para forçar comentários (Loop Infinito)
COMMENT_QUESTIONS = [
    "Isso foi cálculo ou pura sorte?",
    "Dava pra jogar melhor?",
    "Qual campeão você mais odeia jogar contra?",
    "De 0 a 10, que nota essa jogada merece?",
    "Você tiltaria se morresse pra essa play?",
    "O que você faria se estivesse no lugar dele?"
]

def get_video_info(video_path: str):
    """Obtém duração, resolução e fps do vídeo usando ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,r_frame_rate",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        raise RuntimeError(f"Erro ao analisar vídeo com ffprobe: {result.stderr}")
    
    data = json.loads(result.stdout)
    duration = None
    if "format" in data and "duration" in data["format"]:
        duration = float(data["format"]["duration"])
    elif "streams" in data and len(data["streams"]) > 0 and "duration" in data["streams"][0]:
        duration = float(data["streams"][0]["duration"])
    else:
        duration = 20.0  # fallback se não conseguir detectar
        
    width = int(data["streams"][0].get("width", 1920))
    height = int(data["streams"][0].get("height", 1080))
    
    return {
        "duration": duration,
        "width": width,
        "height": height
    }

def get_system_font(size: int, bold: bool = True):
    """Tenta carregar fonte Impact ou Arial Black/Bold do Windows ou fontes equivalentes no Linux."""
    candidates = [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\ariblk.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw):
    """Quebra texto em múltiplas linhas para caber na largura especificada."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w > max_width and len(current_line) > 1:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines

def create_hook_overlay(text: str, badge_text: str = "ORGANIZAÇÃO ESPORTS", output_path: str = None):
    """Cria uma imagem PNG transparente 1080x1920 com o texto do Gancho (0s a 3s)."""
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Badge superior da equipe / organização
    badge_font = get_system_font(32)
    badge_bbox = draw.textbbox((0, 0), badge_text.upper(), font=badge_font)
    bw = badge_bbox[2] - badge_bbox[0] + 40
    bh = badge_bbox[3] - badge_bbox[1] + 20
    bx = (1080 - bw) // 2
    by = 240
    
    # Fundo do badge com cantos arredondados
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=15, fill=(15, 23, 42, 220), outline=(234, 179, 8, 255), width=3)
    draw.text((bx + 20, by + 10), badge_text.upper(), font=badge_font, fill=(255, 255, 255, 255))
    
    # 2. Texto principal do Gancho (Amarelo / Branco, Caixa Alta, Impact)
    hook_font = get_system_font(74)
    lines = wrap_text(text.upper(), hook_font, 920, draw)
    
    start_y = by + bh + 40
    line_height = 85
    
    for i, line in enumerate(lines):
        line_bbox = draw.textbbox((0, 0), line, font=hook_font)
        lw = line_bbox[2] - line_bbox[0]
        lx = (1080 - lw) // 2
        ly = start_y + (i * line_height)
        
        # Sombra projetada preta
        draw.text((lx + 6, ly + 6), line, font=hook_font, fill=(0, 0, 0, 240))
        
        # Borda preta grossa (stroke)
        draw.text((lx, ly), line, font=hook_font, fill=(255, 230, 0, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        
    if not output_path:
        output_path = str(ASSETS_DIR / "hook_temp.png")
    img.save(output_path, "PNG")
    return output_path

def create_outro_overlay(question: str, output_path: str = None):
    """Cria uma imagem PNG transparente 1080x1920 com a pergunta de retenção/comentários (últimos 3s)."""
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Badge inferior "💬 RESPONDE AÍ:"
    badge_font = get_system_font(36)
    badge_text = "💬 RESPONDE AÍ:"
    b_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = b_bbox[2] - b_bbox[0] + 40
    bh = b_bbox[3] - b_bbox[1] + 20
    bx = (1080 - bw) // 2
    by = 1380
    
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=15, fill=(20, 20, 20, 230), outline=(255, 230, 0, 255), width=3)
    draw.text((bx + 20, by + 10), badge_text, font=badge_font, fill=(255, 230, 0, 255))
    
    # Pergunta em destaque
    q_font = get_system_font(60)
    lines = wrap_text(question, q_font, 920, draw)
    
    start_y = by + bh + 30
    line_height = 70
    for i, line in enumerate(lines):
        line_bbox = draw.textbbox((0, 0), line, font=q_font)
        lw = line_bbox[2] - line_bbox[0]
        lx = (1080 - lw) // 2
        ly = start_y + (i * line_height)
        
        # Sombra
        draw.text((lx + 4, ly + 4), line, font=q_font, fill=(0, 0, 0, 240))
        # Texto com borda preta
        draw.text((lx, ly), line, font=q_font, fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255))
        
    if not output_path:
        output_path = str(ASSETS_DIR / "outro_temp.png")
    img.save(output_path, "PNG")
    return output_path

def generate_hook_and_comment(champion: str = None, detail: str = None, category: str = "random"):
    """Gera o texto do gancho e a pergunta final com base nos parâmetros."""
    if not champion:
        champion = "ESSE MONSTRO"
    if not detail:
        detail = "100 DE HP"
        
    if category == "random" or category not in HOOK_TEMPLATES:
        category = random.choice(["provocacao", "desafio", "mecanica"])
        
    template = random.choice(HOOK_TEMPLATES[category])
    hook_text = template.format(champion=champion, detail=detail)
    comment_text = random.choice(COMMENT_QUESTIONS)
    
    return hook_text, comment_text

def render_vertical_gameplay(
    input_video_path: str,
    output_video_path: str,
    champion: str = None,
    detail: str = None,
    hook_text: str = None,
    comment_text: str = None,
    badge_text: str = "PLAY DA EQUIPE",
    tension_start: float = 3.0,
    tension_end: float = 8.0,
    hook_duration: float = 3.5,
    outro_duration: float = 3.5
):
    """
    Renderiza o vídeo 9:16 vertical (1080x1920) com:
    - Fundo com blur e escurecido
    - Gameplay centralizada nítida
    - Zoom cinematográfico gradual durante o build-up (3s a 8s)
    - Overlay de Gancho (0s a 3.5s)
    - Overlay de Comentários / Retenção (últimos segundos)
    - Efeito sonoro de impacto Whoosh no segundo 0
    - Loop infinito seco
    """
    input_video_path = Path(input_video_path).resolve()
    output_video_path = Path(output_video_path).resolve()
    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    
    info = get_video_info(input_video_path)
    duration = info["duration"]
    
    # Se os textos não foram passados diretamente, gera com base no campeão e detalhe
    if not hook_text or not comment_text:
        auto_hook, auto_comment = generate_hook_and_comment(champion, detail)
        hook_text = hook_text or auto_hook
        comment_text = comment_text or auto_comment
        
    # Gera as imagens PNG dos overlays
    hook_img_path = str(ASSETS_DIR / f"hook_{os.getpid()}.png")
    outro_img_path = str(ASSETS_DIR / f"outro_{os.getpid()}.png")
    
    create_hook_overlay(hook_text, badge_text=badge_text, output_path=hook_img_path)
    create_outro_overlay(comment_text, output_path=outro_img_path)
    
    whoosh_path = str(AUDIO_DIR / "whoosh.wav")
    has_whoosh = os.path.exists(whoosh_path)
    
    # Calcula os tempos para os overlays
    outro_start = max(0.0, duration - outro_duration)
    
    # Efeito de Zoom Gradual no gameplay entre tension_start e tension_end:
    # Aumenta suavemente de 1080 de largura para ~1240 (115% de zoom) e corta para 1080x608
    # Fórmula: zoom = 1 + 0.15 * ((t - tension_start) / (tension_end - tension_start))
    # Para evitar complexidade excessiva de expressão no FFmpeg, usamos uma animação com zoompan ou scale interp
    
    filter_complex = [
        # 1. Camada de Fundo Otimizada (Renderiza 5x mais rápido fazendo o blur em baixa resolução antes de esticar)
        "[0:v]scale=180:320:force_original_aspect_ratio=increase,crop=180:320,boxblur=6:2,scale=1080:1920:flags=fast_bilinear,eq=brightness=-0.12[bg];",
        
        # 2. Camada da Gameplay Principal (centro):
        # Durante t entre 3s e 8s, aplica zoom sutil de até 115%
        f"[0:v]scale=eval=frame:w='if(between(t,{tension_start},{tension_end}), 1080*(1+0.03*(t-{tension_start})), if(gt(t,{tension_end}), 1080*1.15, 1080))':h=-1,crop=1080:608:(iw-1080)/2:(ih-608)/2[fg];",
        
        # 3. Sobrepõe a gameplay no centro do fundo (y=656 é o centro vertical exato)
        "[bg][fg]overlay=0:656[comp1];",
        
        # 4. Sobrepõe o Gancho Visual nos primeiros hook_duration segundos
        f"[comp1][1:v]overlay=0:0:enable='between(t,0,{hook_duration})'[comp2];",
        
        # 5. Sobrepõe a Pergunta de Encerramento nos últimos outro_duration segundos
        f"[comp2][2:v]overlay=0:0:enable='gte(t,{outro_start})'[vout]"
    ]
    
    inputs = [
        "-i", str(input_video_path),
        "-loop", "1", "-i", str(hook_img_path),
        "-loop", "1", "-i", str(outro_img_path)
    ]
    
    # Mix de áudio com whoosh (se existir)
    if has_whoosh:
        inputs.extend(["-i", whoosh_path])
        audio_filter = ";[0:a][3:a]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        filter_str = "".join(filter_complex) + audio_filter
        audio_maps = ["-map", "[aout]"]
    else:
        filter_str = "".join(filter_complex)
        audio_maps = ["-map", "0:a?"]
        
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[vout]",
        *audio_maps,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_video_path)
    ]
    
    print(f"Iniciando renderização de: {input_video_path.name}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if proc.returncode != 0:
            print("Erro FFmpeg:", proc.stderr)
            raise RuntimeError(f"FFmpeg falhou com código {proc.returncode}")
        print(f"Vídeo renderizado com sucesso: {output_video_path}")
        return {
            "success": True,
            "output_path": str(output_video_path),
            "hook_text": hook_text,
            "comment_text": comment_text,
            "duration": duration
        }
    finally:
        # Limpa imagens temporárias
        for p in [hook_img_path, outro_img_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

if __name__ == "__main__":
    print("Módulo de edição carregado com sucesso.")
