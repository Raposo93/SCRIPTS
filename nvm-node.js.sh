#!/bin/zsh

# Variables para almacenar las instalaciones realizadas
instalaciones_realizadas=()

# Instalar NVM y Node.js
if ! command -v nvm &>/dev/null; then
    # Instalación de NVM
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | zsh
    source ~/.zshrc
    echo "NVM instalado."
    instalaciones_realizadas+=("NVM")
else
    echo "NVM ya está instalado."
fi

# Instalar Node.js 18.17.1
if command -v nvm &>/dev/null; then
    nvm install 18.17.1
    nvm use 18.17.1
    echo "Node.js 18.17.1 instalado y configurado."
    instalaciones_realizadas+=("Node.js 18.17.1")
else
    echo "NVM no está instalado. No se puede instalar Node.js."
fi

# Mostrar resumen de las instalaciones realizadas
echo -e "\nResumen de instalaciones realizadas:"
if [ ${#instalaciones_realizadas[@]} -ne 0 ]; then
    echo "Herramientas y aplicaciones instaladas:"
    for herramienta in "${instalaciones_realizadas[@]}"; do
        echo "  $herramienta"
    done
fi
