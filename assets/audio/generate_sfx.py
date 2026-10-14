import math
import struct
import wave
import os

def create_whoosh(filename, duration=1.2, sample_rate=44100):
    """Gera um efeito sonoro de Whoosh / Impacto sonoro sintético."""
    num_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        # Envelope de volume: cresce rápido e decai
        if t < 0.2:
            env = (t / 0.2) ** 2
        else:
            env = math.exp(-3.5 * (t - 0.2))
        
        # Frequência varre de 600Hz para baixo até 60Hz (efeito whoosh/drop)
        freq = 60 + 540 * math.exp(-4 * t)
        
        # Onda senoidal + harmônico de grave
        val = 0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * (freq * 0.5) * t)
        
        # Adiciona um pouco de ruído branco filtrado no início para o som de vento do whoosh
        noise = (hash(i) % 1000 / 500.0 - 1.0) * max(0.0, 1.0 - t * 4) * 0.2
        
        sample = int(32767 * max(-1.0, min(1.0, (val + noise) * env)))
        samples.append(sample)
        
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        data = struct.pack('<' + ('h' * len(samples)), *samples)
        wav.writeframes(data)
    print(f"Efeito de áudio gerado com sucesso: {filename}")

if __name__ == "__main__":
    audio_dir = r"C:\Users\Usuário\.gemini\antigravity\scratch\lol-clips-editor\assets\audio"
    create_whoosh(os.path.join(audio_dir, "whoosh.wav"))
