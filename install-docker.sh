#!/bin/zsh

# Verificar e instalar Docker si no está presente
if ! command -v docker &>/dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker instalado"
    rm get-docker.sh
else
    echo "Docker ya está instalado."
fi

# Variables de versión para Docker Compose
DOCKER_COMPOSE_VERSION="1.29.2"

# Verificar e instalar Docker Compose si no está presente
if ! command -v docker-compose &>/dev/null; then
    echo "Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose ${DOCKER_COMPOSE_VERSION} instalado."
else
    echo "Docker Compose ya está instalado."
fi
    echo "Por favor, cierra sesión y vuelve a iniciarla para aplicar los cambios de grupo."
