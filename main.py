#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple inline keyboard bot with multiple CallbackQueryHandlers.

This Bot uses the Updater class to handle the bot.
DEALER, a few callback functions are defined as callback query handler. Then, those functions are
passed to the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot that uses inline keyboard that has multiple CallbackQueryHandlers arranged in a
ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line to stop the bot.

"""
import re
import pandas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler
import logging

import configparser
logger = logging.getLogger(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Stages
DEALER, PLAYER_CARD_ONE, PLAYER_CARD_TWO, STRATEGY, ADD_CARD, \
    DEALER_CARD, START, ADD_CARD = range(8)

# PLAYER CONTROLLER
USERS = {}

STRATEGY_LEGEND = {
    "P": "SPLIT",
    "S": "STAND",
    "H": "HIT",
    "D": "DOUBLE DOWN",
    "Sr": "Not sure"
}

player_history = []


def inline(key):
    return InlineKeyboardButton(key, callback_data=str(key))


card_keyboard = [[inline('2'), inline('3'), inline('4')],
                 [inline('5'), inline('6'), inline('7')],
                 [inline('8'), inline('9'), inline('10')],
                 [inline('Ace')]]

card_markup = InlineKeyboardMarkup(card_keyboard)

df = pandas.read_csv('basicstrategy_hit_soft17.csv')


def calculate_basic_strategy(CURRENT_CONTEXT):
    print(CURRENT_CONTEXT)
    if 'A' in CURRENT_CONTEXT["player_cards"] or len(set(CURRENT_CONTEXT["player_cards"])) == 1:
        player = ''.join(CURRENT_CONTEXT["player_cards"])
    else:
        player = CURRENT_CONTEXT["player_total"]
    print(f'Player: {player}')
    dealer = CURRENT_CONTEXT["dealer_card"]
    player_moves = df[df['Player'] == f'{player}']
    print(player_moves)
    print(f'Dealer: {dealer}')
    print(player_moves[f'{dealer}'].values[0])
    dealer_moves = player_moves[f'{dealer}'].values[0]
    print(f'You should: {STRATEGY_LEGEND[dealer_moves]}')
    return STRATEGY_LEGEND[dealer_moves]


def process_card_value(card, CURRENT_CONTEXT, isDealer=False, calculateStrategy=False):
    value = 0

    if card == 'Ace':
        value = 11
        card = 'A'
    elif isinstance(int(card), int):
        value = int(card)

    if isDealer:
        CURRENT_CONTEXT["dealer_card"] = card
    else:
        CURRENT_CONTEXT["player_total"] += int(value)
        CURRENT_CONTEXT["player_cards"].append(card)

    if calculateStrategy:
        CURRENT_CONTEXT["player_cards"] = sorted(
            CURRENT_CONTEXT["player_cards"], key=lambda x: (x[0].isdigit(), x))
        CURRENT_CONTEXT["strategy"] = calculate_basic_strategy(CURRENT_CONTEXT)
    return CURRENT_CONTEXT


def start(update, context):
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    global USERS
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    PLAYER_TEMPLATE = {
        "round": 1,
        "username": user.username,
        "player_cards": [],
        "player_total": 0,
        "dealer_card": "",
        "strategy": ""
    }
    USERS[user.username] = PLAYER_TEMPLATE
    CURRENT_CONTEXT = USERS[user.username]

    # New Round message
    message = f'New Round! Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]} \nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\nReady? '

    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup([[inline('New Round')]])
    )

    # Tell ConversationHandler that we're in state `DEALER` now
    return PLAYER_CARD_ONE


def player_card_one_choice(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_CONTEXT = USERS[user.username]
    message = f'Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]}\nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\nChoose Your 1st Card: '
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    return PLAYER_CARD_TWO


def player_card_two_choice(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_USER = USERS[user.username]
    CURRENT_CONTEXT = process_card_value(query.data, CURRENT_USER)
    message = f'Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]}\nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\nChoose Your 2nd Card: '
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    return DEALER_CARD


def dealer_card_choice(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_USER = USERS[user.username]
    CURRENT_CONTEXT = process_card_value(query.data, CURRENT_USER)
    message = f'Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]}\nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\nChoose Dealers Card: '
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    # Tell ConversationHandler that we're in state `STRATEGY` now
    return STRATEGY


def confirm_data(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_USER = USERS[user.username]
    CURRENT_CONTEXT = process_card_value(query.data, CURRENT_USER, True, True)
    message = f'Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]}\nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\n'
    message = message + f'You should: *{CURRENT_CONTEXT["strategy"]}* \n\n'
    message = message + f'Choose the action you took: '
    keyboard = [
        [inline(CURRENT_USER["strategy"])],
        [inline('Something Else')],
        [inline('New Round')]
    ]

    strategy_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=strategy_markup
    )

    # Tell ConversationHandler that we're in state `STRATEGY` now
    return STRATEGY


def add_card(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_CONTEXT = USERS[user.username]
    message = f'Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]}\nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\n You {query.data}! New card?'
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    return ADD_CARD


def confirm_new_card(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_USER = USERS[user.username]
    CURRENT_CONTEXT = process_card_value(query.data, CURRENT_USER, False, True)
    print("COnfirm New data")
    message = f'Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]}\nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\n'
    message = message + f'You should: *{CURRENT_CONTEXT["strategy"]}* \n\n'
    message = message + f'Choose the action you took: '
    keyboard = [
        [inline(CURRENT_USER["strategy"])],
        [inline('Something Else')],
        [inline('New Round')]
    ]

    strategy_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=strategy_markup
    )

    # Tell ConversationHandler that we're in state `STRATEGY` now
    return STRATEGY


def start_over(update, context):
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    global USERS
    query = update.callback_query
    if query.message.reply_to_message:
        user = query.message.reply_to_message.from_user
    else:
        user = query.message.chat
    bot = context.bot
    CURRENT_CONTEXT = USERS[user.username]
    round_up = CURRENT_CONTEXT['round'] + 1
    player_name = CURRENT_CONTEXT['username']

    USERS[user.username] = {
        "round": round_up,
        "username": user.username,
        "player_cards": [],
        "player_total": 0,
        "dealer_card": "",
        "strategy": ""
    }

    CURRENT_CONTEXT = USERS[user.username]

    # New Round message
    message = f'New Round! Round: {CURRENT_CONTEXT["round"]} ({CURRENT_CONTEXT["username"]}) \nDealers Card: {CURRENT_CONTEXT["dealer_card"]} \nYour Cards: {CURRENT_CONTEXT["player_cards"]} \nYour total: {CURRENT_CONTEXT["player_total"]} \n\nReady? '

    # Send message with text and appended InlineKeyboard
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=InlineKeyboardMarkup([[inline('New Round')]])
    )

    # Tell ConversationHandler that we're in state `DEALER` now
    return PLAYER_CARD_ONE


def end(update, context):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over"""
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="See you next time!"
    )
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['DEFAULT']['BOT_TOKEN'], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Setup conversation handler with the states DEALER and PLAYER
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(start_over, pattern='^New Round$')],

            DEALER_CARD: [CallbackQueryHandler(dealer_card_choice)],

            PLAYER_CARD_ONE: [CallbackQueryHandler(player_card_one_choice)],

            PLAYER_CARD_TWO: [CallbackQueryHandler(player_card_two_choice)],

            STRATEGY: [CallbackQueryHandler(confirm_data, pattern='^([1-9]|Ace)$'),
                       CallbackQueryHandler(
                           start_over, pattern='^(Something Else|New Round)$'),
                       CallbackQueryHandler(
                           add_card, pattern='^(HIT|DOUBLE DOWN)$')],

            ADD_CARD: [CallbackQueryHandler(confirm_new_card, pattern='^([1-9]|Ace)$')],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    # Add ConversationHandler to dispatcher that will be used for handling
    # updates
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
