#!/usr/bin/env python3
"""
🎯 EXEMPLO PRÁTICO - CALCULADORA INTERATIVA
Este é um exemplo para você aprender Python de forma prática!
"""

# Importações - aqui trazemos funcionalidades extras
import os
from datetime import datetime

# Função para limpar a tela (funciona em Linux/Mac/Windows)
def limpar_tela():
    os.system('clear' if os.name == 'posix' else 'cls')

# Função para mostrar o menu
def mostrar_menu():
    print("\n" + "="*50)
    print("🧮 CALCULADORA INTERATIVA 🧮".center(50))
    print("="*50)
    print("\nEscolha uma operação:")
    print("1. ➕ Somar")
    print("2. ➖ Subtrair")
    print("3. ✖️  Multiplicar")
    print("4. ➗ Dividir")
    print("5. 📊 Ver histórico")
    print("6. 🚪 Sair")
    print("\n" + "="*50)

# Lista para guardar o histórico de cálculos
historico = []

# Função para adicionar ao histórico
def adicionar_historico(operacao, num1, num2, resultado):
    hora = datetime.now().strftime("%H:%M:%S")
    historico.append(f"[{hora}] {num1} {operacao} {num2} = {resultado}")

# Função principal da calculadora
def calculadora():
    while True:
        limpar_tela()
        mostrar_menu()
        
        # Pega a escolha do usuário
        try:
            escolha = input("\n👉 Digite sua escolha (1-6): ")
            
            if escolha == '6':
                print("\n👋 Até logo! Foi bom calcular com você!")
                break
            
            if escolha == '5':
                print("\n📜 HISTÓRICO DE CÁLCULOS:")
                if historico:
                    for calc in historico:
                        print(f"   {calc}")
                else:
                    print("   Nenhum cálculo realizado ainda!")
                input("\nPressione ENTER para continuar...")
                continue
            
            if escolha in ['1', '2', '3', '4']:
                # Pega os números
                num1 = float(input("Digite o primeiro número: "))
                num2 = float(input("Digite o segundo número: "))
                
                # Faz o cálculo baseado na escolha
                if escolha == '1':
                    resultado = num1 + num2
                    operacao = "+"
                    print(f"\n✅ Resultado: {num1} + {num2} = {resultado}")
                    
                elif escolha == '2':
                    resultado = num1 - num2
                    operacao = "-"
                    print(f"\n✅ Resultado: {num1} - {num2} = {resultado}")
                    
                elif escolha == '3':
                    resultado = num1 * num2
                    operacao = "*"
                    print(f"\n✅ Resultado: {num1} × {num2} = {resultado}")
                    
                elif escolha == '4':
                    if num2 != 0:
                        resultado = num1 / num2
                        operacao = "/"
                        print(f"\n✅ Resultado: {num1} ÷ {num2} = {resultado:.2f}")
                    else:
                        print("\n❌ Erro: Não é possível dividir por zero!")
                        input("\nPressione ENTER para continuar...")
                        continue
                
                # Adiciona ao histórico
                adicionar_historico(operacao, num1, num2, resultado)
                
                input("\nPressione ENTER para continuar...")
            else:
                print("\n❌ Opção inválida! Tente novamente.")
                input("\nPressione ENTER para continuar...")
                
        except ValueError:
            print("\n❌ Por favor, digite apenas números!")
            input("\nPressione ENTER para continuar...")
        except KeyboardInterrupt:
            print("\n\n👋 Programa interrompido. Até logo!")
            break
        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")
            input("\nPressione ENTER para continuar...")

# Ponto de entrada do programa
if __name__ == "__main__":
    print("🚀 Bem-vindo ao exemplo prático do Cursor!")
    print("Este programa demonstra conceitos básicos de Python:")
    print("- Funções")
    print("- Loops")
    print("- Condicionais (if/else)")
    print("- Tratamento de erros")
    print("- Listas")
    print("- Entrada/saída de dados")
    
    input("\nPressione ENTER para começar...")
    
    # Chama a função principal
    calculadora()

# 💡 DICAS DE ESTUDO:
# 1. Tente modificar este código! Por exemplo:
#    - Adicione uma operação de potência (x²)
#    - Mude as cores ou emojis
#    - Adicione uma função para calcular porcentagem
#
# 2. Para executar este programa, peça:
#    "Execute o arquivo exemplo_pratico.py"
#
# 3. Se tiver dúvidas sobre alguma parte, pergunte:
#    "Explique como funciona a linha X"
#    "O que faz a função Y?"