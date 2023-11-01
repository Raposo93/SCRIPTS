#!/bin/bash

# Variables para almacenar las instalaciones realizadas
instalaciones_realizadas=()

# Instalar Zsh si no está presente
if ! command -v zsh &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y zsh
    echo "Zsh instalado."
    instalaciones_realizadas+=("Zsh")
else
    echo "Zsh ya está instalado."
fi

# Establecer Zsh como shell predeterminada si está instalado
if command -v zsh &>/dev/null; then
    chsh -s $(which zsh)
    echo "Zsh establecido como shell predeterminada."
fi

# Instalar Oh My Zsh si Zsh está instalado
if command -v zsh &>/dev/null; then
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
        echo "Oh My Zsh instalado."
        instalaciones_realizadas+=("Oh My Zsh")
    else
        echo "Oh My Zsh ya está instalado."
    fi
fi

# Descargar el tema Powerlevel10k si Oh My Zsh está instalado
if [ -d "$HOME/.oh-my-zsh" ]; then
    if [ ! -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k" ]; then
        git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
        echo "Tema Powerlevel10k descargado. Por favor, configúralo manualmente ejecutando 'p10k configure'."
    else
        echo "El tema Powerlevel10k ya está descargado."
    fi
fi

# Mostrar resumen de las instalaciones realizadas
echo -e "\nResumen de instalaciones realizadas:"
if [ ${#instalaciones_realizadas[@]} -ne 0 ]; then
    echo "Herramientas y aplicaciones instaladas:"
    for herramienta in "${instalaciones_realizadas[@]}"; do
        echo "  $herramienta"
    done
fi
