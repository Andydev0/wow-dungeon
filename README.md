# 🐉 WoW Dungeon - Discord Bot de Notificação de Dungeons Míticas

![Discord](https://img.shields.io/badge/Discord-Bot-blue?style=flat-square&logo=discord)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

`WoW Dungeon` é um bot de Discord para jogadores de World of Warcraft que envia notificações sobre dungeons míticas completadas pelo personagem vinculado. Com uma interface simples e comandos fáceis de usar, o bot permite que você gerencie suas notificações de maneira personalizada.

## 🚀 Funcionalidades

- **🔗 Vinculação de Personagens:** Vincule seus personagens usando o comando `/add_char`.
- **⏰ Notificações Automáticas:** Receba notificações privadas sobre dungeons completadas após a última terça-feira.
- **🛠️ Comandos de Gerenciamento:** Edite, exclua e liste seus personagens vinculados.
- **📬 Testes de Notificação:** Teste manualmente as notificações para todos os seus personagens vinculados.

## 📋 Pré-requisitos

- Python 3.11+
- Um bot do Discord configurado com o token
- Conta na API Raider.IO

## 🛠️ Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/Andydev0/wow-dungeon.git
cd wow-dungeon
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto e adicione o token do bot do Discord:

```env
DISCORD_TOKEN=seu_token_aqui
```

### 3. Instalar Dependências

Instale as dependências necessárias com o comando:

```bash
pip install -r requirements.txt
```

### 4. Executar o Bot

Inicie o bot com o seguinte comando:

```bash
python wow-dungeon.py
```

## 💻 Comandos Disponíveis

- **`/add_char`** - Vincula um personagem para notificações.
- **`/verificar_chars`** - Lista todos os personagens vinculados.
- **`/editar_char`** - Edita as configurações de notificação de um personagem.
- **`/deletar_char`** - Remove um personagem vinculado.
- **`/testar_notificacao`** - Testa a notificação de um personagem vinculado.
- **`/testar_todas_notificacoes`** - Testa as notificações de todos os personagens vinculados.

## 📦 Dependências

- **discord.py** - Interação com a API do Discord.
- **apscheduler** - Agendamento das notificações.
- **python-dotenv** - Gerenciamento de variáveis de ambiente.
- **requests** - Requisições HTTP para a API Raider.IO.

## 🌐 Hospedagem

O bot pode ser hospedado em qualquer serviço de hospedagem de Python que suporte websockets, como Heroku, AWS, ou um VPS.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests para melhorias.

## 📝 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
