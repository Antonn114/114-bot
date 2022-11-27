import asyncio
import os
import logging
import discord
import math
import random
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
load_dotenv(find_dotenv())

bot = commands.Bot(command_prefix='::', intents=discord.Intents.all())


# utils
async def send_response(ctx, subject, response, formatted: bool = True):
    logging.info(
        f'Query {ctx.message.content.split()[0][len(bot.command_prefix):]} ({subject}) from {ctx.author} -> Sent "{response}" as response.')
    if formatted:
        await ctx.send(f'```\n{response}\n```')
    else:
        await ctx.send(f'\n{response}\n')


def show_board(board):
    board_display = ''
    for row in board:
        for square in row:
            board_display += '[' + square + '] '
        board_display += '\n'
    return board_display


# commands

@bot.command(name='latency')
async def get_latency(ctx):
    await send_response(ctx, None, f'{bot.latency * 1000} ms')


@bot.command(name='avatar')
async def avatar(ctx, *args: discord.User):
    for i in args:
        try:
            x = i.avatar.url
        except Exception as error:
            logging.error(f"{error} occurred! - Query aborted.")
            continue
        await send_response(ctx, i, x, False)


@bot.command(name='ttt')
async def ttt(ctx):
    # init

    x, o, n = 'x', 'o', ' '
    board = [[n, n, n], [n, n, n], [n, n, n]]
    value = {
        'x': 1,
        'o': -1,
        ' ': 0
    }

    def flag(m):
        return m.channel == ctx.channel and m.author == ctx.author

    def check_for_winner():
        my_winner = None
        for i in range(len(board)):
            if all(board[i][j] == board[i][0] for j in range(len(board[i]))) and board[i][0] != ' ':
                my_winner = board[i][0]
        for j in range(len(board)):
            if all(board[i][j] == board[0][j] for i in range(len(board[j]))) and board[0][j] != ' ':
                my_winner = board[0][j]
        if all(board[i][i] == board[0][0] for i in range(len(board))) and board[0][0] != ' ':
            my_winner = board[0][0]
        if all(board[i][len(board) - i - 1] == board[0][-1] for i in range(len(board))) and board[0][-1] != ' ':
            my_winner = board[0][-1]

        finished = True
        for this_row in board:
            for square in this_row:
                if square == n:
                    finished = False
        if finished and my_winner is None:
            return ' '
        else:
            return my_winner

    def my_move(depth: int, maximising: bool):
        my_winner = check_for_winner()
        if my_winner is not None:
            return [value[my_winner]]

        legal_moves = []
        for i in range(len(board)):
            for j in range(len(board)):
                if board[i][j] == n:
                    legal_moves.append((i, j))

        this_move = [1, 1]
        if maximising:
            best_score = -math.inf

            for node in legal_moves:
                board[node[0]][node[1]] = x
                score = my_move(depth + 1, False)
                board[node[0]][node[1]] = n
                if score[0] >= best_score:
                    best_score = score[0]
                    this_move = node

            if depth == 0:
                return this_move
            else:
                return [best_score]
        else:
            best_score = math.inf

            for node in legal_moves:
                board[node[0]][node[1]] = o
                score = my_move(depth + 1, True)
                board[node[0]][node[1]] = n
                if score[0] <= best_score:
                    best_score = score[0]
                    this_move = node

            if depth == 0:
                return this_move
            else:
                return [best_score]

    await send_response(ctx, "Start game", "For each input there should only be one line with r and c as integers (1 "
                                           "<= r, c <= 3), where r denotes the row and c denotes the column of your "
                                           "move.\nRespond with 'x' or 'o' (without quotes) to start your game as the "
                                           "corresponding player (x starts first)")

    player_selection_message = await bot.wait_for('message', timeout=20.0, check=flag)
    if player_selection_message.content.lower() not in ['x', 'o']:
        await send_response(ctx, "Wrong Args", "Invalid response! Game aborted.")
        return

    player = player_selection_message.content.lower()
    if player == o:
        selection_move = my_move(0, True)
        board[selection_move[0]][selection_move[1]] = x

    while check_for_winner() is None:
        await send_response(ctx, None, show_board(board))
        message = await bot.wait_for('message', timeout=20.0, check=flag)
        if message.content.upper() == "QUIT":
            break
        response_args = message.content.split()
        if not (len(response_args) == 2 and response_args[0].isdigit() and response_args[1].isdigit()):
            await send_response(ctx, "Wrong Args", "Invalid response! Please pick a valid spot.")
            continue
        row, col = [int(i) for i in response_args]
        if board[row - 1][col - 1] != n:
            await send_response(ctx, "Position Already Occupied",
                                "Position is already occupied! Please pick another one.")
            continue
        board[row - 1][col - 1] = player

        winner = check_for_winner()
        if winner is not None:
            break
        move = my_move(0, player == o)
        if player == x:
            board[move[0]][move[1]] = o
        else:
            board[move[0]][move[1]] = x

    await send_response(ctx, None, show_board(board))
    winner = check_for_winner()
    if winner is None:
        await send_response(ctx, 'Game over!', f'Game aborted!')
    elif value[winner]:
        await send_response(ctx, 'Game over!', f'{check_for_winner()} won!')
    else:
        await send_response(ctx, 'Game over!', "it's a tie!")


@bot.event
async def on_ready():
    logging.info(f'Successfully logged in as {bot.user}.')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await send_response(ctx, f'ERROR: {error}', 'Invalid Arguments - Query ignored.')
    if isinstance(error, asyncio.TimeoutError):
        await send_response(ctx, f'ERROR: {error}', 'Coroutine timed out.')


bot.run(os.environ.get("CLIENT_TOKEN"))
