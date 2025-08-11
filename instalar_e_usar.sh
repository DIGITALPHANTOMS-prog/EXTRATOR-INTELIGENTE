#!/bin/bash

echo "🎰 MegaMania - Instalação e Uso"
echo "================================"

# Instalar dependências
echo "📦 Instalando dependências..."
pip3 install --break-system-packages selenium pandas

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "📋 COMO USAR:"
echo ""
echo "1. Crie um arquivo 'cpfs.txt' com um CPF por linha"
echo ""
echo "2. Execute o script Selenium:"
echo "   python3 megamania_selenium.py"
echo ""
echo "3. Os resultados serão salvos em 'resultados_megamania.csv'"
echo ""
echo "================================"