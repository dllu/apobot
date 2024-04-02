import os
from collections import defaultdict
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

guild_id = 1062107664932417586
role_id = 1224746856077332692
apo_emoji_id = 1070609258233741373
rules_message_id = 1062298391658377247
mod_channel_id = 1224815581316780183


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
    await grant_role_to_active_users(guild_id, role_id)
    await ctx.send("Role assignment process initiated.")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.id == apo_emoji_id and payload.message_id == rules_message_id:
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


user_messages = defaultdict(list)


def clean_up_old_timestamps(now):
    one_minute_ago = now - timedelta(minutes=1)

    for key, timestamps in list(user_messages.items()):
        # Keep only timestamps that are less than a minute old
        new_timestamps = [
            timestamp for timestamp in timestamps if timestamp > one_minute_ago
        ]

        if new_timestamps:
            user_messages[key] = new_timestamps
        else:
            # If no timestamps are left for this message content, remove the content key
            del user_messages[key]


@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    now = datetime.utcnow()
    content = message.content
    user_id = message.author.id
    key = f"{user_id}-{hash(content)}"

    # Add the timestamp of the current message to the tracking structure
    user_messages[key].append(now)
    clean_up_old_timestamps(now)

    mod_channel = bot.get_channel(mod_channel_id)

    # Check if this message was posted more than 6 times within the last 60 seconds
    if len(user_messages[key]) > 6:
        first_message_time = user_messages[key][0]
        if now - first_message_time < timedelta(seconds=60):  # Within 60 seconds
            try:
                # Ban the user
                await message.author.ban(
                    reason="Spamming the same message in multiple channels"
                )

                guild = bot.get_guild(guild_id)
                if guild is None:
                    print("Guild not found.")
                    return

                for channel in guild.text_channels:
                    await message.channel.purge(
                        limit=100, check=lambda m: m.author == message.author
                    )
                mod_channel.send(f"Banned {message.author} for spamming.")

            except discord.Forbidden:
                print(f"Failed to ban {message.author} - I might not have permission.")
            except discord.HTTPException:
                print(f"Failed to ban {message.author} due to an HTTP error.")

    await bot.process_commands(message)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


token = os.getenv("APOBOT_TOKEN")
print("Discord token:", token)
bot.run(token)
