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
DEALER, PLAYER_CARD_ONE, PLAYER_CARD_TWO, STRATEGY = range(4)

# Callback data
ONE, TWO, THREE, FOUR = range(4)

# ROUND CONTROLLER
ROUND = 0
PLAYER_TOTAL = 0

PLAYER_LAYOUT = {
    "player_cards": [],
    "player_total": "",
    "dealer_card": "",
    "strategy": ""
}

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


def calculate_basic_strategy():
    df = pandas.read_csv('basicstrategy_hit_soft17.csv')
    player = ''.join(PLAYER_LAYOUT["player_cards"])
    dealer = PLAYER_LAYOUT["dealer_card"]
    player_moves = df[df['Player'] == player]
    print(player_moves)
    print(f'{dealer}')
    print(player_moves[f'{dealer}'])
    dealer_moves = player_moves[f'{dealer}'].values[0]
    return STRATEGY_LEGEND[dealer_moves]


def process_card_value(card, isDealer=False):

    global PLAYER_TOTAL
    value = 0

    if card == 'Ace':
        value = 11
        card = 'A'
    elif isinstance(int(card), int):
        value = int(card)

    if isDealer:
        PLAYER_LAYOUT["dealer_card"] = value
        PLAYER_LAYOUT["strategy"] = calculate_basic_strategy()
    else:
        PLAYER_TOTAL = PLAYER_TOTAL + value
        PLAYER_LAYOUT["player_total"] = PLAYER_TOTAL
        PLAYER_LAYOUT["player_cards"].append(card)


def start(update, context):
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    global ROUND, PLAYER_LAYOUT, PLAYER_TOTAL
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [[InlineKeyboardButton("Enter Your Cards", callback_data=str(ONE))],
                [InlineKeyboardButton("New Round", callback_data=str(THREE))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ROUND += 1
    PLAYER_TOTAL = 0
    player_history.append(PLAYER_LAYOUT)
    PLAYER_LAYOUT = {
        "player_cards": [],
        "player_total": "",
        "dealer_card": ""
        "strategy": ""
    }

    # New Round message
    message = f'New Round! Round: {ROUND} \nDealers Card: {PLAYER_LAYOUT["dealer_card"]} \nYour Cards: {PLAYER_LAYOUT["player_cards"]} \nYour total: {PLAYER_LAYOUT["player_total"]} \n\nReady? '

    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        message,
        reply_markup=reply_markup
    )

    # Tell ConversationHandler that we're in state `DEALER` now
    return PLAYER_CARD_ONE


def dealer_card_choice(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    bot = context.bot
    process_card_value(query.data)
    message = f'Round: {ROUND} \nDealers Card: {PLAYER_LAYOUT["dealer_card"]}\nYour Cards: {PLAYER_LAYOUT["player_cards"]} \nYour total: {PLAYER_LAYOUT["player_total"]} \n\nChoose Dealers Card: '
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    # Tell ConversationHandler that we're in state `STRATEGY` now
    return STRATEGY


def player_card_one_choice(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    bot = context.bot
    message = f'Round: {ROUND} \nDealers Card: {PLAYER_LAYOUT["dealer_card"]}\nYour Cards: {PLAYER_LAYOUT["player_cards"]} \nYour total: {PLAYER_LAYOUT["player_total"]} \n\nChoose Your 1st Card: '
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
    bot = context.bot
    process_card_value(query.data)
    message = f'Round: {ROUND} \nDealers Card: {PLAYER_LAYOUT["dealer_card"]}\nYour Cards: {PLAYER_LAYOUT["player_cards"]} \nYour total: {PLAYER_LAYOUT["player_total"]} \n\nChoose Your 2nd Card: '
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    return DEALER


def confirm_data(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    bot = context.bot
    process_card_value(query.data, True)
    message = f'Round: {ROUND} \nDealers Card: {PLAYER_LAYOUT["dealer_card"]}\nYour Cards: {PLAYER_LAYOUT["player_cards"]} \nYour total: {PLAYER_LAYOUT["player_total"]} \n\n'
    message = message + f'You should: {PLAYER_LAYOUT["strategy"]}'
    keyboard = [
        [inline(PLAYER_LAYOUT["strategy"])],
        [inline('Something else')],
        [InlineKeyboardButton("New Round", callback_data=str(THREE))]
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


def strategy(update, context):
    """Show new choice of buttons"""
    query = update.callback_query
    bot = context.bot
    message = f'New Round! Round: {ROUND} \nDealers Card: \nYour Cards: \nYour total: \n\n'

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=message,
        reply_markup=card_markup
    )

    return STRATEGY


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
            DEALER: [CallbackQueryHandler(
                dealer_card_choice, pattern='^([1-9]|Ace)$'),
                CallbackQueryHandler(
                start, pattern='^' + str(THREE) + '$')],

            PLAYER_CARD_ONE: [CallbackQueryHandler(player_card_one_choice)],

            PLAYER_CARD_TWO: [CallbackQueryHandler(player_card_two_choice)],

            STRATEGY: [CallbackQueryHandler(confirm_data, pattern='^([1-9]|Ace)$'),
                       CallbackQueryHandler(
                           strategy, pattern='^(HIT|STAND|DOUBLE DOWN|SPLIT|Something Else)$'),
                       CallbackQueryHandler(
                start, pattern='^' + str(THREE) + '$')],
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
