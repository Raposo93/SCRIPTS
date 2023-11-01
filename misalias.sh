#!/bin/zsh

# Variables para almacenar los alias actualizados y añadidos con sus comandos
alias_actualizados=()
alias_anadidos=()

# Check if the Zsh config file exists
if [ -f ~/.zshrc ]; then
    # Add or update the 'actualizar' alias
    if grep -q "alias actualizar=" ~/.zshrc; then
        sed -i 's/^alias actualizar=.*$/alias actualizar="sudo apt update \&\& sudo apt upgrade -y";/' ~/.zshrc
        echo "'actualizar' alias updated in ~/.zshrc."
        alias_actualizados+=("actualizar = sudo apt update && sudo apt upgrade -y")
    else
        echo 'alias actualizar="sudo apt update && sudo apt upgrade -y";' >> ~/.zshrc
        echo "'actualizar' alias added to ~/.zshrc."
        alias_anadidos+=("actualizar = sudo apt update && sudo apt upgrade -y")
    fi

    # Add or update the 'instalar' alias
    if grep -q "alias instalar=" ~/.zshrc; then
        sed -i 's/^alias instalar=.*$/alias instalar="sudo apt install";/' ~/.zshrc
        echo "'instalar' alias updated in ~/.zshrc."
        alias_actualizados+=("instalar = sudo apt install")
    else
        echo 'alias instalar="sudo apt install";' >> ~/.zshrc
        echo "'instalar' alias added to ~/.zshrc."
        alias_anadidos+=("instalar = sudo apt install")
    fi

    # Add or update the 'permitir' alias
    if grep -q "alias permitir=" ~/.zshrc; then
        sed -i 's/^alias permitir=.*$/alias permitir="chmod +x";/' ~/.zshrc
        echo "'permitir' alias updated in ~/.zshrc."
        alias_actualizados+=("permitir = chmod +x")
    else
        echo 'alias permitir="chmod +x";' >> ~/.zshrc
        echo "'permitir' alias added to ~/.zshrc."
        alias_anadidos+=("permitir = chmod +x")
    fi

    # Source the updated ~/.zshrc to apply changes
    source ~/.zshrc

    # Mostrar resumen de los alias actualizados y añadidos con sus comandos
    echo -e "\nResumen de cambios:"

    if [ ${#alias_actualizados[@]} -ne 0 ]; then
        echo "Alias actualizados:"
        for alias in "${alias_actualizados[@]}"; do
            echo -e "  $alias"
        done
    fi

    if [ ${#alias_anadidos[@]} -ne 0 ]; then
        echo "Alias añadidos:"
        for alias in "${alias_anadidos[@]}"; do
            echo -e "  $alias"
        done
    fi

    # Reload the console to apply the changes immediately
    exec zsh
else
    echo "Zsh configuration file ~/.zshrc not found. Please make sure you are using Zsh."
fi
