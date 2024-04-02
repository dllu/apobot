import os
from datetime import datetime, timedelta

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def grant_role_to_active_users(guild_id, role_id):
    """
    automatically adds APO role to people who have posted in past week
    """
    try:
        # Find the guild by ID
        guild = bot.get_guild(guild_id)
        if guild is None:
            print("Guild not found.")
            return

        # Find the role in the guild by ID
        role = discord.utils.get(guild.roles, id=role_id)
        if role is None:
            print("Role not found.")
            return

        one_week_ago = datetime.utcnow() - timedelta(weeks=1)
        active_users = set()

        # Iterate through all text channels in the guild
        for channel in guild.text_channels:
            try:
                # Use history() to fetch messages from the last week
                async for message in channel.history(limit=None, after=one_week_ago):
                    # Add the user ID to the set of active users (if not a bot)
                    if not message.author.bot:
                        if message.author not in active_users:
                            print("Found active author:", message.author)
                        active_users.add(message.author)
            except discord.errors.Forbidden:
                print(f"Cannot access history for {channel.name}, skipping.")
                continue

        # Assign the role to each active user
        for user in active_users:
            try:
                if role not in user.roles:
                    await user.add_roles(role)
                    print(f"Assigned {role.name} to {user.display_name}")
            except Exception as e2:
                print(f"Couldn't assign role to {user}: {e2}")

        print("Role assignment complete.")

    except Exception as e:
        print(f"An error occurred: {e}")


@bot.command(name="assignroles")
async def assign_roles_command(ctx):
    guild_id = 1062107664932417586
    role_id = 1224746856077332692
    await grant_role_to_active_users(guild_id, role_id)
    await ctx.send("Role assignment process initiated.")


@bot.event
async def on_raw_reaction_add(payload):
    apo_emoji_id = 1070609258233741373
    message_id = 1062298391658377247
    if payload.emoji.id == apo_emoji_id and payload.message_id == message_id:
        role_id = 1224746856077332692
        try:
            user = await bot.fetch_user(payload.user_id)
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                print(f"Adding {role.name} to {user.name}")
                # Add the role to the user
                await member.add_roles(role)
                print(f"Added {role.name} to {user.name}")
        except Exception as e2:
            print(f"Couldn't assign role to {user}: {e2}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


token = os.getenv("DISCORD_TOKEN")
print("Discord token:", token)
bot.run(token)
