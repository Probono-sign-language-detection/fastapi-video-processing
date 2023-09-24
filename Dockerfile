FROM python:3.10-slim-buster

WORKDIR /app

ENV APP_HOME=/app

# 필요한 패키지 복사
COPY requirements.txt ./

# pdf, vim ffmpeg 설치
RUN apt-get update && apt-get install -y bash && apt-get install -y build-essential\
    && apt-get install -y libgl1-mesa-glx vim\
    && apt-get install -y ffmpeg \  
    && apt-get install -y wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Install Xvfb and other dependencies for headless browser testing
RUN apt-get update \
    && apt-get install -y wget gnupg2 libgtk-3-0 libdbus-glib-1-2 dbus-x11 xvfb ca-certificates

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

EXPOSE 8000

# app user 생성 및 모든 파일 권한변경
RUN useradd -m app && chown -R app:app $APP_HOME

USER app