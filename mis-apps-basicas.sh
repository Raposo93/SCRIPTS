#!/bin/zsh

# Variables para almacenar las instalaciones realizadas
instalaciones_realizadas=()

# Función para verificar e instalar con apt-get
verificar_instalar_apt() {
    if ! command -v $1 &>/dev/null; then
        sudo apt-get install -y $1
        echo "$1 instalado."
        instalaciones_realizadas+=("$1")
    else
        echo "$1 ya está instalado."
    fi
}

sudo apt update && sudo apt upgrade -y
verificar_instalar_apt "git"
verificar_instalar_apt "curl"
verificar_instalar_apt "tilix"
verificar_instalar_apt "docker.io"
verificar_instalar_apt "docker-compose"
verificar_instalar_apt "linphone-desktop"
# Añadir usuario al grupo docker
sudo usermod -aG docker $USER
echo "Usuario agregado al grupo 'docker'."

# Instalar SDKMAN!
if [ ! -d "$HOME/.sdkman" ]; then
    curl -s "https://get.sdkman.io" | bash
    source "$HOME/.sdkman/bin/sdkman-init.sh"
    echo "SDKMAN! instalado."
    instalaciones_realizadas+=("SDKMAN!")
else
    echo "SDKMAN! ya está instalado."
fi
source "$HOME/.sdkman/bin/sdkman-init.sh"

sdk install java 17.0.8-tem
instalaciones_realizadas+=("Java 17.0.8-tem")

sdk install maven 3.9.0
instalaciones_realizadas+=("Maven 3.9.0")

# Comprobar y desinstalar Firefox si está instalado
if whereis firefox | grep -q apt; then
    sudo apt-get remove firefox
    echo "Firefox desinstalado."
elif whereis firefox | grep -q snap; then
    sudo snap remove firefox
    echo "Firefox snap desinstalado."
else
    echo "Firefox no está instalado."
fi

# Instalar ultimo firefox sin snap ni apt
curl -L -o ~/Firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64"
    sudo tar xjf ~/Firefox.tar.bz2 -C /opt/
    rm ~/Firefox.tar.bz2
    sudo ln -s /opt/firefox/firefox /usr/bin
    echo "Firefox descargado e instalado en /opt/"

    instalaciones_realizadas+=("Firefox")

echo -e "\nResumen de instalaciones realizadas:"
if [ ${#instalaciones_realizadas[@]} -ne 0 ]; then
    echo "Herramientas y aplicaciones instaladas:"
    for herramienta in "${instalaciones_realizadas[@]}"; do
        echo "  $herramienta"
    done
fi

# Reload the console to apply the changes immediately
exec zsh
