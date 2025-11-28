import os
import sys
import threading
import moviepy.editor as mp
import whisper
import pysrt
from tkinter import Tk, filedialog, Label, Button, StringVar, IntVar, Text, Scrollbar, END, RIGHT, Y
from tkinter import ttk

# ---------- Função principal ----------
def gerar_legenda():
    global progress_var, status_var, text_widget

    video_path = filedialog.askopenfilename(
        title="Selecione o vídeo",
        filetypes=[("Vídeos", "*.mp4 *.avi *.mkv *.mov *.flv")]
    )
    if not video_path:
        status_var.set("Nenhum vídeo selecionado.")
        root.update()
        print("Nenhum vídeo selecionado.")
        return

    status_var.set("Extraindo áudio...")
    root.update()
    print("Extraindo áudio...")
    try:
        video = mp.VideoFileClip(video_path)
        if not video.audio:
            status_var.set("Erro: o vídeo não contém áudio.")
            root.update()
            print("Erro: o vídeo não contém áudio.")
            return

        audio_path = "temp_audio.wav"
        video.audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec='pcm_s16le', logger=None)
    except Exception as e:
        status_var.set(f"Erro ao extrair áudio: {e}")
        root.update()
        print(f"Erro ao extrair áudio: {e}")
        return

    if not os.path.exists(audio_path):
        status_var.set("Erro: áudio não foi gerado.")
        root.update()
        print("Erro: áudio não foi gerado.")
        return

    status_var.set("Carregando modelo Whisper...")
    root.update()
    print("Carregando modelo Whisper...")
    try:
        model = whisper.load_model("small")
    except Exception as e:
        status_var.set(f"Erro ao carregar modelo: {e}")
        root.update()
        print(f"Erro ao carregar modelo: {e}")
        return

    status_var.set("Transcrevendo áudio para português...")
    root.update()
    print("Transcrevendo áudio para português...")
    try:
        result = model.transcribe(audio_path, language="pt")
        segments = result['segments']
    except Exception as e:
        status_var.set(f"Erro na transcrição: {e}")
        root.update()
        print(f"Erro na transcrição: {e}")
        return

    if not segments:
        status_var.set("Nenhum segmento gerado. Transcrição falhou.")
        root.update()
        print("Nenhum segmento gerado. Transcrição falhou.")
        return

    status_var.set("Gerando legenda em tempo real...")
    root.update()
    print("Gerando legenda em tempo real...")

    subs = pysrt.SubRipFile()
    total_segments = len(segments)
    text_widget.delete("1.0", END)

    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip().replace("\n", " ")

        # Inserir no campo de texto e rolar automaticamente
        text_widget.insert(END, text + "\n")
        text_widget.see(END)
        root.update()  # equivalente ao Application.ProcessMessages
        print(text)   # escreve também no console

        # Atualizar barra de progresso
        progress_var.set(int((i+1)/total_segments*100))
        root.update()

        # Criar item SRT
        sub = pysrt.SubRipItem(
            index=i+1,
            start=pysrt.SubRipTime(seconds=start),
            end=pysrt.SubRipTime(seconds=end),
            text=text
        )
        subs.append(sub)

    if getattr(sys, 'frozen', False):
        pasta = os.path.dirname(sys.executable)
    else:
        pasta = os.path.dirname(os.path.abspath(__file__))

    nome_arquivo = os.path.splitext(os.path.basename(video_path))[0] + ".srt"
    srt_path = os.path.join(pasta, nome_arquivo)
    try:
        subs.save(srt_path, encoding='utf-8')
    except Exception as e:
        status_var.set(f"Erro ao salvar SRT: {e}")
        root.update()
        print(f"Erro ao salvar SRT: {e}")
        return

    status_var.set(f"Legenda salva em: {srt_path}")
    progress_var.set(100)
    root.update()
    print(f"Legenda salva em: {srt_path}")

    if os.path.exists(audio_path):
        os.remove(audio_path)

# ---------- Criar GUI ----------
root = Tk()
root.title("Legendas Automáticas")
root.geometry("750x500")

status_var = StringVar()
status_var.set("Aguardando vídeo...")

progress_var = IntVar()

# ---------- Layout com Frames ----------

# Botão no topo
frame_button = ttk.Frame(root)
frame_button.pack(pady=10)
Button(frame_button, text="Selecionar vídeo e gerar legenda",
       command=lambda: threading.Thread(target=gerar_legenda).start(),
       width=40).pack()

# Título
frame_title = ttk.Frame(root)
frame_title.pack(pady=10)
Label(frame_title, text="Legendas Automáticas (Whisper + Filmora)", font=("Arial", 16)).pack()

# Status
frame_status = ttk.Frame(root)
frame_status.pack(pady=5)
status_label = Label(frame_status, textvariable=status_var)
status_label.pack()

# Progresso
frame_progress = ttk.Frame(root)
frame_progress.pack(pady=10)
progress = ttk.Progressbar(frame_progress, orient="horizontal", length=700, mode="determinate",
                           maximum=100, variable=progress_var)
progress.pack()

# Campo de texto com scroll
frame_text = ttk.Frame(root)
frame_text.pack(pady=10, fill="both", expand=True)

scrollbar = Scrollbar(frame_text)
scrollbar.pack(side=RIGHT, fill=Y)

text_widget = Text(frame_text, wrap="word", yscrollcommand=scrollbar.set)
text_widget.pack(fill="both", expand=True)
scrollbar.config(command=text_widget.yview)

# ---------- Iniciar GUI ----------
root.mainloop()
