"""
Conquest cog.
"""

import math
import time
import asyncio
import discord
from discord.ext import commands

VIEW_TIMEOUT = 60 * 15 # time before main view times out for inactivity
START_TROOPS = 100 # starting troop count
START_ECO = 10 # starting eco
REFRESH_TIME = 10 # wait interval time between eco giving troops
KILL_RATIO = 0.75 # troops vs troops ratio lost for defending player, max 8 chars
ECO_COST = 3 # how much 1 eco costs in terms of troops
EVENT_LIMIT = 10 # number of events to show
TROOPS_ICON = '🔫'
ECO_ICON = '💵'
DEAD_ICON = '☠️'
MAX_PLAYERS = 10 # max number of players that can join the same game
                 # max is 20 due to attacking players is made with limited chars

def ordinal(n):
  if 11 <= (n % 100) <= 13:
    suffix = 'th'
  else:
    suffix = ('th', 'st', 'nd', 'rd', 'th')[min(n % 10, 4)]
  return str(n) + suffix

class InputModal(discord.ui.Modal):
  def __init__(self, game_view, player, title, label, extra = None):
    super().__init__(title = title)
    self.game_view = game_view
    self.player = player
    self.item = discord.ui.TextInput(
      label = label[:45],
      placeholder = 'Type a number, e.g. "10"',
      required = True,
      min_length = 1,
      max_length = 5
    )
    self.add_item(self.item)
    if extra: # got lazy
      self.add_item(extra)

  async def on_submit(self, interaction):
    if self.player.id in self.game_view.losers:
      return await interaction.response.send_message('Detected that you lost the game. Click **Refresh** to update.', ephemeral = True)
    elif not self.item.value.isdecimal():
      return await interaction.response.send_message('Bad input! (Must be a number only)', ephemeral = True)
    self.interaction = interaction
      
class ConquestGameView(discord.ui.View):
  def __init__(self, game_view, player):
    super().__init__()
    self.player = player
    self.game_view = game_view
    self.update_embed()
  
  def update_embed(self):
    if self.player.id in self.game_view.losers:
      lost = True
      place = ordinal(len(self.game_view.players) - self.game_view.losers.index(interaction.user.id))
      description = 'You lost the game `{}`. ({} place)'.format(DEAD_ICON, place)
    else:
      lost = False
      troops, eco = self.game_view.data[self.player.id]
      description = '\n'.join([
        'You have `{}` **{:,} troops**.'.format(TROOPS_ICON, troops),
        'You have `{}` **{:,} eco**.'.format(ECO_ICON, eco),
        '',
        'Next refresh: <t:{}:R>'.format(self.game_view.last_refresh + REFRESH_TIME)
      ])
    self.embed = discord.Embed(
      title = '{}\'s Empire'.format(self.player.name),
      description = description,
      color = discord.Color.blurple()
    )
    self.embed.add_field(
      name = 'Events',
      value = '\n'.join(reversed(self.game_view.events[-EVENT_LIMIT:]))
    )
    leaderboard = [
      '{}. <@{}>\'s Empire - `{}` {:,} | `{}` {:,}'.format(index + 1, player_id, ECO_ICON, eco, TROOPS_ICON, troops)
      for index, (player_id, (troops, eco)) in enumerate(sorted(
        self.game_view.data.items(),
        key = lambda x: x[1][1]
      ))
    ]
    for loser_id in reversed(self.game_view.losers):
      text = '{}. <@{}>\'s Empire - `{}` DEAD'.format(len(leaderboard) + 1, loser_id, DEAD_ICON)
      leaderboard.append(text)
    self.embed.add_field(
      name = 'Leaderboard',
      value = '\n'.join(leaderboard)
    )
    return lost

  @discord.ui.button(label = 'Refresh', style = discord.ButtonStyle.blurple)
  async def refresh_button(self, interaction, button):
    if self.update_embed(): # lost during refresh
      self.stop()
      await interaction.response.edit_message(embed = self.embed, view = None)
      self.game_view.views.remove(self)
      return
    await interaction.response.edit_message(embed = self.embed)

  @discord.ui.button(label = 'Eco', style = discord.ButtonStyle.blurple)
  async def eco_button(self, interaction, button):
    if self.player.id in self.game_view.losers:
      return await interaction.response.send_message('Detected that you lost the game. Click **Refresh** to update.', ephemeral = True)
    modal = InputModal(self.game_view, self.player, 'Eco Modal', 'Type N troops to sacrifice for eco. (XR {}:1)'.format(ECO_COST))
    await interaction.response.send_modal(modal)
    self.game_view.modals.add(modal)
    await modal.wait()
    self.game_view.modals.remove(modal)
    if not hasattr(modal, 'interaction'): # failed
      return
    data = self.game_view.data[self.player.id]
    if data[0] < ECO_COST:
      return await modal.interaction.response.send_message('Insufficent troops to buy more eco.', ephemeral = True)
    count = int(modal.item.value) // ECO_COST
    if not count:
      return await modal.interaction.response.send_message('Failed because min troops to spend is {}.'.format(ECO_COST), ephemeral = True)
    cost = count * ECO_COST
    if data[0] < cost: 
      return await modal.interaction.response.send_message('Failed because you need `{}` troops to buy `{}` eco.'.format(cost, count), ephemeral = True)
    data[0] -= cost # troops
    data[1] += count # eco
    text = '{} spent {} troops on {} eco.'.format(self.player.mention, cost, count)
    self.game_view.log_event(text)
    self.update_embed() # alr checked
    await modal.interaction.response.edit_message(embed = self.embed)
    
  @discord.ui.button(label = 'Attack', style = discord.ButtonStyle.blurple)
  async def attack_button(self, interaction, button):
    if self.player.id in self.game_view.losers:
      return await interaction.response.send_message('Detected that you lost the game. Click **Refresh** to update.', ephemeral = True)
    choices = [
      player
      for player in self.game_view.players
      if player.id not in self.game_view.losers # lost already
      and player.id != interaction.user.id # themself
    ]
    placeholder = '\n'.join(
      '{} {}'.format(index + 1, player.name[:3])
      for index, player in enumerate(choices)
    )
    extra = discord.ui.TextInput(
      label = 'Who to attack? Type the number only.',
      placeholder = placeholder,
      required = True,
      min_length = 1,
      max_length = 2
    )
    modal = InputModal(self.game_view, self.player, 'Attack Modal', 'Type N troops to attack with. (XR {}:1)'.format(KILL_RATIO), extra)
    await interaction.response.send_modal(modal)
    self.game_view.modals.add(modal)
    await modal.wait()
    self.game_view.modals.remove(modal)
    if not hasattr(modal, 'interaction'): # failed
      return
    elif not extra.value.isdecimal():
      return await modal.interaction.response.send_message('Bad input! (Must be a number only)', ephemeral = True)
    val = int(extra.value)
    player = choices[val-1:val]
    if not player:
      return await modal.interaction.response.send_message('Invalid target player choice.', ephemeral = True)
    player = player[0]
    data = self.game_view.data[self.player.id]
    troops = int(modal.item.value)
    if data[0] < troops:
      return await modal.interaction.response.send_message('Insufficent troops to attack with.', ephemeral = True)
    elif player.id in self.game_view.losers:
      return await modal.interaction.response.send_message('Target player already lost the game.', ephemeral = True)
    target_data = self.game_view.data[player.id]
    target_data[0] -= math.ceil(troops * KILL_RATIO)
    data[0] -= troops
    text = '{} attacked {} with {} troops.'.format(interaction.user.mention, player.mention, troops)
    self.game_view.log_event(text)
    won = False
    if target_data[0] < 0: # target dead
      data[0] += target_data[0] * -1
      eco = target_data[1]
      data[1] += eco
      self.game_view.losers.append(player.id)
      del self.game_view.data[player.id]
      text = '{} destroyed {}, inherting {} eco.'.format(interaction.user.mention, player.mention, eco)
      self.game_view.log_event(text)
      won = await self.game_view.check_win(interaction.user.id) # last man standing...
    self.update_embed() # alr checked
    if won:
      self.embed.description += '\nCongrats, you won!'
      return await modal.interaction.response.edit_message(embed = self.embed, view = None)
    await modal.interaction.response.edit_message(embed = self.embed)
    
class ConquestMainView(discord.ui.View):
  def __init__(self, host):
    super().__init__(timeout = VIEW_TIMEOUT)
    self.remove_item(self.view_button)
    self.host = host
    self.players = {host}
    self.task = None
    self.views = {self}
    self.modals = set()
    self.embed = discord.Embed(
      title = 'Conquest: Lobby',
      description = '\n'.join([
        '{} is hosting a new Conquest game.'.format(host.mention),
        '',
        'Click **Join** to join the game.'
      ]),
      color = discord.Color.blurple()
    )
    self.embed.add_field(
      name = 'Players',
      value = host.mention
    )

  def log_event(self, text):
    now = int(time.time())
    diff = now - self.start
    mins, secs = divmod(diff, 60)
    self.events.append('[`{}:{:02}`] {}'.format(mins, secs, text))
    
  async def refresh_task(self):
    while True:
      await asyncio.sleep(REFRESH_TIME)
      for key in self.data:
        self.data[key][0] += self.data[key][1] # add #eco to #troops
      self.last_refresh = int(time.time())
      self.log_event('Eco refreshed!')

  async def on_timeout(self):
    for obj in self.views | self.modals:
      obj.stop()
    if self.task:
      self.task.cancel()

  async def check_win(self, winner_id):
    if len(self.data) == 1:
      for obj in self.views | self.modals:
        obj.stop()
      self.task.cancel()
      troops, eco = self.data[winner_id]
      self.log_event('<@{}> won the game with {} troops and {} eco!'.format(winner_id, troops, eco))
      leaderboard = [winner_id] + self.losers
      self.embed.title = 'Conquest: Ended'
      self.embed.description = 'The winner is <@{}>, GG!'.format(winner_id)
      self.embed.set_field_at(
        0,
        name = 'Final Leaderboard',
        value = '\n'.join(
          '{}. <@{}>'.format(index + 1, player_id)
          for index, player_id in enumerate(leaderboard)
        )
      )
      try:
        await self.original_interaction.edit_original_response(embed = self.embed, view = None)
      except discord.HTTPException:
        pass
      return True
    
  @discord.ui.button(label = 'Abort Game', style = discord.ButtonStyle.red)
  async def abort_button(self, interaction, button):
    if interaction.user != self.host:
      return await interaction.response.send_message('Denied because you are not the host.', ephemeral = True)
    for obj in self.views | self.modals:
      obj.stop()
    if self.task: # ongoing game
      self.task.cancel()
    self.embed.set_footer(text = 'Game was cancelled by the host.')
    await interaction.response.edit_message(embed = self.embed, view = None)

  @discord.ui.button(label = 'Join', style = discord.ButtonStyle.blurple)
  async def join_button(self, interaction, button):
    if interaction.user in self.players:
      return await interaction.response.send_message('You already joined the game.', ephemeral = True)
    elif len(self.players) == MAX_PLAYERS:
      return await interaction.response.send_message('Max players reached ({}).'.format(MAX_PLAYERS), ephemeral = True)
    self.players.add(interaction.user)
    self.embed.set_field_at(
      0,
      name = 'Players',
      value = '\n'.join(map(lambda x: x.mention, self.players))
    )
    await interaction.response.edit_message(embed = self.embed)
    
  @discord.ui.button(label = 'Start Game', style = discord.ButtonStyle.green)
  async def start_button(self, interaction, button):
    if interaction.user != self.host:
      return await interaction.response.send_message('Denied because you are not the host.', ephemeral = True)
    elif len(self.players) == 1:
      return await interaction.response.send_message('Need at least 2 players to start.', ephemeral = True)
    self.remove_item(self.join_button)
    self.remove_item(button)
    self.remove_item(self.help_button)
    self.add_item(self.view_button)
    self.add_item(self.help_button)
    self.data = {
      player.id : [START_TROOPS, START_ECO] # [troops, eco]
      for player in self.players
    }
    self.events = ['[`0:00`] Game started.'] # lists because these have to be ordered
    self.losers = []
    self.original_interaction = interaction
    self.embed.title = 'Conquest: Started'
    self.embed.description = '\n'.join([
      '{} has started the game!'.format(self.host.mention),
      '',
      'Click **View** to view your empire.'
    ])
    self.start = self.last_refresh = int(time.time())
    self.task = asyncio.create_task(self.refresh_task())
    await interaction.response.edit_message(embed = self.embed, view = self)
    
  @discord.ui.button(emoji = '❔', label = 'Help', style = discord.ButtonStyle.blurple)
  async def help_button(self, interaction, button):
    await interaction.response.send_message('Tutorial: bla', ephemeral = True)
    
  @discord.ui.button(label = 'View', style = discord.ButtonStyle.blurple)
  async def view_button(self, interaction, button):
    if interaction.user not in self.players:
      return await interaction.response.send_message('You didn\'t join the game.', ephemeral = True)
    elif interaction.user.id in self.losers:
      place = ordinal(len(self.players) - self.losers.index(interaction.user.id))
      return await interaction.response.send_message('You lost the game `{}`. ({} place)'.format(DEAD_ICON, place), ephemeral = True)
    view = ConquestGameView(self, interaction.user)
    self.views.add(view)
    await interaction.response.send_message(embed = view.embed, view = view, ephemeral = True)
  
class Conquest(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  @commands.is_owner()
  async def conquest(self, ctx):
    view = ConquestMainView(ctx.author)
    await ctx.send(embed = view.embed, view = view)

async def setup(bot):
  await bot.add_cog(Conquest(bot))
