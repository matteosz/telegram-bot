import logging, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    MessageHandler, 
    filters, 
    CommandHandler, 
    ConversationHandler,
    Application,
    CallbackQueryHandler
)
from dotenv import load_dotenv
from multiprocessing import Process
from string_process import tokenize
from tracker import track_product
from notify import send_text
from s3 import list_all_files, download_file, upload_file

def preprocess():

    global TOKEN, HEROKU_LINK, PORT, MENU, REGISTER1, REGISTER2, DELETE, CLOCK, logger, BUCKET_NAME

    # Enable logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    load_dotenv() # load vars in .env

    TOKEN = str(os.getenv('BOT_TOKEN'))
    HEROKU_LINK = str(os.getenv('HEROKU'))
    PORT = int(os.environ.get('PORT', 5000))
    BUCKET_NAME = str(os.getenv('S3_BUCKET_NAME'))
    MENU, REGISTER1, REGISTER2, DELETE = range(4)
    CLOCK = 1800 # seconds -> 30min

    # download files from AWS S3 bucket
    files = list_all_files(BUCKET_NAME)
    for file in files:
        if file[-1] == '/':
            # Generate the directory if not present
            current_directory = os.getcwd()
            final_directory = os.path.join(current_directory, file[:-1])
            if not os.path.exists(final_directory):
                os.makedirs(final_directory)
        else:
            download_file(file,BUCKET_NAME,file)

async def start(update, context): # After /start command display main menu

    if update.message:
        await update.message.reply_text(main_menu_message(update),
                                reply_markup=main_menu_keyboard())
        username = update.message.from_user.username
        mex = update.message
    else:
        query = update.callback_query
        await query.answer()
        username = query.from_user.username
        mex = query.message
        await query.edit_message_text(main_menu_message(update),
                                reply_markup=main_menu_keyboard())

    if not running[0]:
        id_chat[0] = mex.chat.id
        resume_trackers()
        running[0] = True

    logger.info("User %s started the main menu", username)
    return MENU

async def stop(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Bye! Type /start whenever you're ready again")
    logger.info("User %s ended the conversation.", query.from_user.username)
    return ConversationHandler.END

# Exit, empty the product list and stop all the trackings -> gives problems when hosted
async def exit(update, context):
    await update.message.reply_text(exit_message(),
                                reply_markup=ReplyKeyboardRemove())
    
    with open('product_list.txt','w+') as openfile:
        openfile.write('')
    for item in trackers.items():
        item.terminate()

    raise KeyboardInterrupt

async def first_menu(update,context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
                        text=first_menu_message(),
                        reply_markup=first_menu_keyboard())
    logger.info("User %s started the registration menu", query.from_user.username)
    return REGISTER1

async def second_menu(update,context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
                        text=second_menu_message(),
                        reply_markup=second_menu_keyboard())
    logger.info("User %s started the cancelation menu", query.from_user.username)
    return DELETE

# Keyboards 
def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Monitor new product', callback_data='m1')],
              [InlineKeyboardButton('Forget old product', callback_data='m2')],
              [InlineKeyboardButton('Exit conversation', callback_data='stop')]]
    return InlineKeyboardMarkup(keyboard)
def first_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)
def second_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Main menu', callback_data='main')]]
    try:
        with open('product_list.txt','r') as openfile:
            lines = openfile.readlines()
            for i in range(len(lines)):
                keyboard.append([InlineKeyboardButton(lines[i].split(',')[0], callback_data='button'+str(i))])
    except:
        pass
    return InlineKeyboardMarkup(keyboard)

# Messages
def main_menu_message(update):
    try:
        user = 'Hi @' + update.message.from_user["username"] + '!'
    except:
        user = 'Back here!'
    return f'{user}\nI\'m a tracker bot and I\'m here to help you.\nWhat do you want to do?'
def first_menu_message():
    return 'To monitor a product type it in a message or go back'
def second_menu_message():
    return 'Tap on the products you want to forget or go back'
def exit_message():
    return 'Shutting down the system...'

async def register1(update, context):
    user = update.message.from_user
    text = update.message.text
    logger.info("Message from %s: %s", user.username, text)

    text = ' '.join(tokenize(text))

    try:
        with open('product_list.txt','a+') as openfile:
            openfile.write(text + ', ')
    except: 
        pass

    await update.message.reply_text('Type the threshold price to trigger the alerts (in EUR):')

    return REGISTER2

async def register2(update, context):
    user = update.message.from_user
    threshold = update.message.text
    logger.info("Message from %s: %s", user.username, threshold)

    try:
        with open('product_list.txt','a') as openfile:
            openfile.write(threshold + '\n')

        with open('product_list.txt','r') as openfile:
            search = openfile.readlines()[-1].split(',')[0]
        threshold = int(threshold)

        # Start the tracking on a separate process
        key = search.replace(' ','_')
        trackers[key] = Process(target=track_product, args=(search,threshold,id_chat[0],CLOCK))
        trackers[key].start()
        
        await update.message.reply_text('Product registered correctly, tracking is started! Returning to main menu...')

    except: 
        await update.message.reply_text('Error occurred in updating the db! Returning to main menu...')

    await update.message.reply_text(main_menu_message(update),
                            reply_markup=main_menu_keyboard())

    return MENU

async def delete(update, context):
    query = update.callback_query
    await query.answer()
    button_number = int(query.data[6:]) # skip the word button - 6 chars

    logger.info("%s pushed the %d° button", query.from_user.username, button_number+1)

    with open('product_list.txt','r') as openfile:
        lines = openfile.readlines()
    new_lines = []
    for i in range(len(lines)):
        if button_number != i:
            new_lines.append(lines[i])

    # Stop the tracking of the product
    key = lines[button_number].split(',')[0].replace(' ','_')
    try:
        trackers[key].terminate()
    except KeyboardInterrupt as e:
        logger.error(e)
    
    with open('product_list.txt','w') as openfile:
        openfile.writelines(new_lines)

    await query.edit_message_text(
                        text=second_menu_message(),
                        reply_markup=second_menu_keyboard())

    return DELETE

def resume_trackers():
    try:
        with open('product_list.txt','r') as openfile:
            lines = openfile.read().splitlines() 

        for line in lines:
            key = line.split(',')[0].replace(' ','_')
            trackers[key] = Process(target=track_product, args=(line.split(',')[0],int(line.split(',')[1][1:]),id_chat[0],CLOCK))
            trackers[key].start()
    except:
        pass

def run():
    application = Application.builder().token(TOKEN).build()

    global trackers, running, id_chat
    trackers, running, id_chat = {}, [False], [-1]

    # Conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(first_menu, pattern='m1'),CallbackQueryHandler(second_menu, pattern='m2'),CallbackQueryHandler(stop, pattern='stop')],
            REGISTER1: [MessageHandler(filters.TEXT, register1), CallbackQueryHandler(start, pattern='main')],
            REGISTER2: [MessageHandler(filters.Regex('^[0-9]+$'), register2)],
            DELETE: [CallbackQueryHandler(start, pattern='main'), CallbackQueryHandler(delete, pattern='button.+')],# pattern is a Regex
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("forcestop", exit))

    # Run the bot until KeyboardInterruption or SystemExit
    #application.run_polling()
    application.run_webhook(listen="0.0.0.0",
                            port = PORT,
                            url_path=TOKEN,
                            webhook_url=HEROKU_LINK+TOKEN)

    # When run_webhook is stopped

    # Save all generated files 
    for file in os.listdir('price_history/'):
        upload_file('price_history/' + file, BUCKET_NAME)
    for file in ['conv_rates.json', 'product_list.txt']:
        upload_file(file, BUCKET_NAME)

    # Send stop message
    send_text('Shut down completed correctly!', id_chat[0])
    print('Application stopped')


if __name__ == '__main__':
    preprocess()
    run()