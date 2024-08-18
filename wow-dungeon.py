import discord
from discord.ext import commands
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import requests
import os
import json
from dotenv import load_dotenv

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Obter as credenciais do arquivo .env
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.guilds = True  # Para capturar eventos de guilda (servidores do discord)
intents.message_content = True

class BotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False
        self.tree = app_commands.CommandTree(self)
        self.guilds_data = self.carregar_dados('guilds.json')
        self.usuarios_personagens = self.carregar_dados('personagens.json')
        self.scheduler = AsyncIOScheduler()

    def carregar_dados(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def salvar_dados(self, data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    async def setup_hook(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True

    async def on_ready(self):
        print(f'Logado como {self.user}')
        self.scheduler.start()

        # Adicionar guilds existentes que não estão no JSON
        for guild in self.guilds:
            if str(guild.id) not in self.guilds_data:
                self.guilds_data[str(guild.id)] = {"guild_name": guild.name}
        self.salvar_dados(self.guilds_data, 'guilds.json')

        # Reagendar todas as notificações dos personagens
        for user_id, personagens in self.usuarios_personagens.items():
            for personagem in personagens:
                self.agendar_notificacao(user_id, personagem)

    async def on_guild_join(self, guild):
        self.guilds_data[str(guild.id)] = {"guild_name": guild.name}
        self.salvar_dados(self.guilds_data, 'guilds.json')
        print(f"Bot entrou no servidor: {guild.name} (ID: {guild.id})")

    def agendar_notificacao(self, user_id, personagem):
        tipo_notificacao = personagem["tipo_notificacao"]
        horario_notificacao = personagem["horario_notificacao"]

        # Mapeamento dos dias da semana do português para o inglês (minúsculo)
        dias_semana = {
            "segunda": "mon",
            "terça": "tue",
            "quarta": "wed",
            "quinta": "thu",
            "sexta": "fri",
            "sábado": "sat",
            "domingo": "sun"
    }

        if tipo_notificacao == "diária":
            # Extrair apenas a hora e minuto
            hour, minute = map(int, horario_notificacao.replace(' UTC', '').split(":")[:2])
            self.scheduler.add_job(self.notificar_dungeons, 'cron', hour=hour, minute=minute, args=[user_id, personagem])
        else:  # Semanal
            try:
                dia_semana, horario = horario_notificacao.split(maxsplit=1)
                dia_semana_en = dias_semana[dia_semana.lower()]  # Converter para inglês abreviado
                hour, minute = map(int, horario.replace(' UTC', '').split(":")[:2])
                self.scheduler.add_job(self.notificar_dungeons, 'cron', day_of_week=dia_semana_en, hour=hour, minute=minute, args=[user_id, personagem])
            except (ValueError, KeyError) as e:
                print(f"Erro no formato de horario_notificacao: {horario_notificacao} - {e}")

    async def notificar_dungeons(self, user_id, personagem):
        user = await self.fetch_user(int(user_id))
        nome_personagem = personagem["nome"]
        servidor = personagem["servidor"]

        info = self.obter_info_personagem(servidor, nome_personagem)
        if 'mythic_plus_recent_runs' in info:
            dungeons = self.filtrar_dungeons_apos_horario(info['mythic_plus_recent_runs'])
            if dungeons:
                await user.send(f'{nome_personagem}-{servidor} completou {len(dungeons)} dungeons essa semana!')
            else:
                await user.send(f'{nome_personagem}-{servidor} não completou nenhuma dungeon essa semana.')
        else:
            await user.send(f"Não foi possível encontrar informações de dungeons míticas recentes para {nome_personagem}-{servidor}.")

    def obter_info_personagem(self, realm, nome_personagem):
        url = f'https://raider.io/api/v1/characters/profile?region=us&realm={realm}&name={nome_personagem}&fields=mythic_plus_recent_runs'
        resposta = requests.get(url)
        return resposta.json()

    def filtrar_dungeons_apos_horario(self, dungeons, dia_semana=1, hora=13):
        agora = datetime.utcnow()
        dias_desde_terca = (agora.weekday() - dia_semana + 7) % 7
        ultima_terca = agora - timedelta(days=dias_desde_terca)
        horario_corte = ultima_terca.replace(hour=hora, minute=0, second=0, microsecond=0)

        dungeons_apos_corte = []
        for dungeon in dungeons:
            completada_em = datetime.fromisoformat(dungeon['completed_at'][:-1])  # Remove o 'Z' do final para parsing
            if completada_em > horario_corte:
                dungeons_apos_corte.append(dungeon)

        return dungeons_apos_corte

client = BotClient()

class DaySelect(discord.ui.Select):
    def __init__(self, interaction, personagem_servidor):
        self.interaction = interaction
        self.personagem_servidor = personagem_servidor
        options = [
            discord.SelectOption(label='Segunda'),
            discord.SelectOption(label='Terça'),
            discord.SelectOption(label='Quarta'),
            discord.SelectOption(label='Quinta'),
            discord.SelectOption(label='Sexta'),
            discord.SelectOption(label='Sábado'),
            discord.SelectOption(label='Domingo')
        ]
        super().__init__(placeholder='Escolha o dia...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        dia_escolhido = self.values[0]
        view = discord.ui.View()
        view.add_item(TimeSelect('semanal', interaction, self.personagem_servidor, dia_escolhido))
        await interaction.response.send_message(f"Escolha o horário para a notificação semanal no dia {dia_escolhido}:", view=view, ephemeral=True)

class TimeSelect(discord.ui.Select):
    def __init__(self, tipo_notificacao, interaction, personagem_servidor, dia_escolhido=None):
        self.tipo_notificacao = tipo_notificacao
        self.interaction = interaction
        self.personagem_servidor = personagem_servidor
        self.dia_escolhido = dia_escolhido
        options = [discord.SelectOption(label=f'{str(hour).zfill(2)}:00 UTC') for hour in range(0, 24)]

        super().__init__(placeholder='Escolha o horário...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        horario_notificacao = self.values[0]
        if self.dia_escolhido:
            horario_notificacao = f"{self.dia_escolhido} {horario_notificacao}"

        user_id = str(interaction.user.id)
        nome, servidor = self.personagem_servidor.split('-')
        personagem_info = {
            "nome": nome,
            "servidor": servidor,
            "tipo_notificacao": self.tipo_notificacao,
            "horario_notificacao": horario_notificacao
        }

        if user_id in client.usuarios_personagens:
            client.usuarios_personagens[user_id].append(personagem_info)
        else:
            client.usuarios_personagens[user_id] = [personagem_info]
        
        client.salvar_dados(client.usuarios_personagens, 'personagens.json')

        client.agendar_notificacao(user_id, personagem_info)

        await interaction.response.send_message(f"Personagem {nome}-{servidor} vinculado com sucesso! Notificações {self.tipo_notificacao} em {horario_notificacao}.", ephemeral=True)

class NotificationTypeSelect(discord.ui.Select):
    def __init__(self, interaction, personagem_servidor):
        self.interaction = interaction
        self.personagem_servidor = personagem_servidor
        options = [
            discord.SelectOption(label='Diária', description='Notificações diárias'),
            discord.SelectOption(label='Semanal', description='Notificações semanais')
        ]
        super().__init__(placeholder='Escolha o tipo de notificação...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        tipo_notificacao = self.values[0].lower()
        view = discord.ui.View()
        if tipo_notificacao == 'diária':
            view.add_item(TimeSelect(tipo_notificacao, interaction, self.personagem_servidor))
            await interaction.response.send_message(f"Escolha o horário para a notificação diária:", view=view, ephemeral=True)
        else:
            view.add_item(DaySelect(interaction, self.personagem_servidor))
            await interaction.response.send_message(f"Escolha o dia para a notificação semanal:", view=view, ephemeral=True)

class CharModal(discord.ui.Modal, title="Vincular Personagem"):
    personagem_servidor = discord.ui.TextInput(label='Personagem-Servidor', placeholder='Ex: Lothgow-Moknathal', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        view = discord.ui.View()
        view.add_item(NotificationTypeSelect(interaction, self.personagem_servidor.value))
        await interaction.response.send_message("Selecione o tipo de notificação para este personagem:", view=view, ephemeral=True)

@client.tree.command(name="add_char", description="Vincule um personagem para notificações")
async def add_char(interaction: discord.Interaction):
    await interaction.response.send_modal(CharModal())

@client.tree.command(name="verificar_chars", description="Verifique seus personagens vinculados")
async def verificar_chars(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in client.usuarios_personagens or not client.usuarios_personagens[user_id]:
        await interaction.response.send_message("Você não tem personagens vinculados.", ephemeral=True)
        return
    
    personagens = client.usuarios_personagens[user_id]
    mensagem = "Seus personagens vinculados:\n"
    for i, personagem in enumerate(personagens, 1):
        mensagem += f"{i}. {personagem['nome']}-{personagem['servidor']} (Notificação: {personagem['tipo_notificacao']} em {personagem['horario_notificacao']})\n"
    
    await interaction.response.send_message(mensagem, ephemeral=True)

@client.tree.command(name="deletar_char", description="Delete um personagem vinculado")
async def deletar_char(interaction: discord.Interaction, nome_servidor: str):
    user_id = str(interaction.user.id)
    if user_id not in client.usuarios_personagens or not client.usuarios_personagens[user_id]:
        await interaction.response.send_message("Você não tem personagens vinculados.", ephemeral=True)
        return

    for personagem in client.usuarios_personagens[user_id]:
        if f"{personagem['nome']}-{personagem['servidor']}" == nome_servidor:
            client.usuarios_personagens[user_id].remove(personagem)
            client.salvar_dados(client.usuarios_personagens, 'personagens.json')
            await interaction.response.send_message(f"Personagem {nome_servidor} removido com sucesso.", ephemeral=True)
            return
    
    await interaction.response.send_message(f"Personagem {nome_servidor} não encontrado.", ephemeral=True)

@client.tree.command(name="editar_char", description="Edite um personagem vinculado")
async def editar_char(interaction: discord.Interaction, nome_servidor: str):
    user_id = str(interaction.user.id)
    if user_id not in client.usuarios_personagens or not client.usuarios_personagens[user_id]:
        await interaction.response.send_message("Você não tem personagens vinculados.", ephemeral=True)
        return

    for personagem in client.usuarios_personagens[user_id]:
        if f"{personagem['nome']}-{personagem['servidor']}" == nome_servidor:
            # Passar o personagem para edição
            view = discord.ui.View()
            view.add_item(NotificationTypeSelect(interaction, nome_servidor))
            await interaction.response.send_message(f"Editando notificações para {nome_servidor}:", view=view, ephemeral=True)
            return
    
    await interaction.response.send_message(f"Personagem {nome_servidor} não encontrado.", ephemeral=True)
    
@client.tree.command(name="testar", description="Testar notificações")
async def testar(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in client.usuarios_personagens or not client.usuarios_personagens[user_id]:
        await interaction.response.send_message("Você não tem personagens vinculados.", ephemeral=True)
        return
    
    personagens = client.usuarios_personagens[user_id][0] # Testar com o primeiro personagem
    await client.notificar_dungeons(user_id, personagens)
    await interaction.response.send_message("Teste enviado com sucesso!", ephemeral=True)
    
@client.tree.command(name="testar_todas", description="Testar todas as notificações")
async def testar_todas(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in client.usuarios_personagens or not client.usuarios_personagens[user_id]:
        await interaction.response.send_message("Você não tem personagens vinculados.", ephemeral=True)
        return
    
    personagens = client.usuarios_personagens[user_id]
    for personagem in personagens:
            await client.notificar_dungeons(user_id, personagem)
        
    await interaction.response.send_message(f"Teste enviado para {personagem['nome']}-{personagem['servidor']} com sucesso!", ephemeral=True)

client.run(DISCORD_TOKEN)
