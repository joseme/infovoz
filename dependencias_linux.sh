# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    portaudio19-dev \
    libasound2-dev \
    mpg123 \
    ffmpeg \
    espeak

# Instala VOSK model español
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip -d ./models/