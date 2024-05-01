#testing v1.2

from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from tabulate import tabulate
from sql_integration import *
from telegram.ext import Application,CommandHandler,ContextTypes,ConversationHandler,MessageHandler,filters, CallbackContext
from bot_functions import delete_coin_from_file, open_trade_csv, BOT_TOKEN_key
from datetime import datetime, timedelta
import os, subprocess, logging


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

SELECT_FILE = 0

async def open_trades(update: Update, context: CallbackContext) -> None:
    if os.path.exists(open_trade_csv):
        df = pd.read_csv(open_trade_csv)
        if df.empty:
            message_text = "No open trades for the moment."
        else:
            grouped = df.groupby('strategy')

            def get_top_and_bottom_trades(group):
                top_trades = group.nlargest(10, 'pnl')
                bottom_trades = group.nsmallest(10, 'pnl')
                return top_trades, bottom_trades

            for strategy, group in grouped:
                message_text = f"Strategy: {strategy}\n"
                top_trades, bottom_trades = get_top_and_bottom_trades(group)
                message_text += "Top Trades:\n\n"
                top_trades['pnl'] = (top_trades['pnl'] * 100).round(2).astype(str) + '%'
                top_trades['probability'] = (top_trades['probability'] * 100).round(0).astype(int).astype(str) + '%'
                top_trades['period_hours'] = (top_trades['period_hours']).round(2).astype(int).astype(str) + 'h'
                message_text += tabulate(top_trades[['trade_id', 'symbol', 'side', 'pnl', 'probability','period_hours']].values.tolist(), tablefmt='plain')
                message_text += "\n\nBottom Trades:\n\n"
                bottom_trades['pnl'] = (bottom_trades['pnl'] * 100).round(2).astype(str) + '%'
                bottom_trades['probability'] = (bottom_trades['probability'] * 100).round(0).astype(int).astype(str) + '%'
                bottom_trades['period_hours'] = (bottom_trades['period_hours']).round(2).astype(int).astype(str) + 'h'
                message_text += tabulate(bottom_trades[['trade_id', 'symbol', 'side', 'pnl', 'probability','period_hours']].values.tolist(), tablefmt='plain')
                await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("No open trades for the moment.")

async def coin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        _, param_str = update.message.text.split("-", 1)
        param_parts = param_str.split("-")
        n = int(param_parts[0])

        df = extract_trade_from_sql(n)

        if df.empty:
            await update.message.reply_text("There is no completed trades yet")
        else:
            # Calculate win rate
            df["Win Rate"] = df['trade_result'].apply(lambda result: 1 if result == "WIN" else 0)
            coin_stats = df.groupby('coin').agg({'Win Rate': 'mean', 'trade_result': 'count'})
            coin_stats.rename(columns={'Win Rate': 'Win Rate (%)', 'trade_result': 'Total Trades'}, inplace=True)
            coin_stats['Win Rate (%)'] = coin_stats['Win Rate (%)'] * 100

            # Convert the percentage string to a float for comparison
            coin_stats['Win Rate Float'] = coin_stats['Win Rate (%)'].astype(float)

            most_performant_coins = coin_stats[coin_stats['Win Rate Float'] >= 75.00].sort_values(by=['Win Rate Float', 'Total Trades'], ascending=[False, False])
            worst_performant_coins = coin_stats[coin_stats['Win Rate Float'] < 75.00].sort_values(by=['Win Rate Float', 'Total Trades'], ascending=[True, False])

            # Select the top and bottom n coins from each category
            top_n_most_performant_coins = most_performant_coins.head(n)
            top_n_worst_performant_coins = worst_performant_coins.head(n)

            # Format win rate as percentage without decimal places using .loc
            top_n_most_performant_coins.loc[:, 'Win Rate (%)'] = top_n_most_performant_coins['Win Rate (%)'].apply(lambda x: "{:.0f}%".format(x))
            top_n_worst_performant_coins.loc[:, 'Win Rate (%)'] = top_n_worst_performant_coins['Win Rate (%)'].apply(lambda x: "{:.0f}%".format(x))

            # Create the messages to send without headers and index label
            most_performant_message = "Most Performant Coins:\n" + top_n_most_performant_coins[['Win Rate (%)', 'Total Trades']].to_string(header=False)
            worst_performant_message = "Worst Performant Coins:\n" + top_n_worst_performant_coins[['Win Rate (%)', 'Total Trades']].to_string(header=False)

            # Send the messages
            await update.message.reply_text(most_performant_message)
            await update.message.reply_text(worst_performant_message)
            
    except ValueError:
        await update.message.reply_text("Invalid command format. Please use /coin-n format.")

async def trade_past(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        _, param_str = update.message.text.split("-", 1)
        param_parts = param_str.split("-")
        past_days = int(param_parts[0])

        df = extract_trade_from_sql(past_days)
        if df.empty:
            await update.message.reply_text("There is no completed trades yet")
        else:
            df['exit_time'] = pd.to_datetime(df['exit_time'], format='%d-%m-%Y %I:%M%p')
            df['entry_time'] = pd.to_datetime(df['entry_time'], dayfirst=True)
            df['open_hour'] = df['entry_time'].dt.strftime('%I %p')
            df['formatted_date'] = df['entry_time'].dt.strftime('%d %B')
            df['period_hours'] = pd.to_numeric(df['period_hours'], errors='coerce')
            df['period_hours'] = df['period_hours'].round(1).astype(str) + ' h'

            # Calculate the cutoff date for filtering
            cutoff_date = datetime.now() - timedelta(days=past_days)

            # Filter the DataFrame
            filtered_trades = df[(df['exit_time'] >= cutoff_date)]

            df_sorted = filtered_trades.sort_values(by='period_hours', ascending=True)

            df_sorted = df_sorted[['trade_id', 'coin', 'side', 'formatted_date', 'strategy', 'trade_result']]

            if df_sorted.empty:
                await update.message.reply_text("No trades match the specified criteria.")
            else:
                formatted_rows = []
                for _, row in df_sorted.iterrows():
                    formatted_row = " | ".join(row.astype(str))
                    formatted_rows.append(formatted_row)
                message = "\n".join(formatted_rows)
                await update.message.reply_text(message)

    except ValueError:
        await update.message.reply_text("Invalid command format. Please use /tradepast-past_days format.")

async def delete_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        _, param_str = update.message.text.split("-", 1)
        coin_to_delete, strategy = param_str.split("-", 1)

        # Assuming you have a function named delete_coin_from_file
        delete_coin_from_file(strategy, coin_to_delete)

        await update.message.reply_text(f"Coin {coin_to_delete} deleted from strategy {strategy}.")

    except ValueError:
        await update.message.reply_text("Invalid command format. Please use /deletecoin-coin-strategy format.")


async def strategy_test_past(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        _, param_str = update.message.text.split("-", 1)
        past_days, rest = param_str.split("-", 1)
        n, strategy = rest.split("-", 1)

        # Convert past_days and n to integers
        past_days = int(past_days)
        n = int(n)
        df = extract_trade_from_sql(past_days)

        if df.empty:
            await update.message.reply_text("There is no completed trades yet")
        else:
            df['exit_time'] = pd.to_datetime(df['exit_time'], format='%d-%m-%Y %I:%M%p')
            df['entry_time'] = pd.to_datetime(df['entry_time'], dayfirst=True)
            df['open_hour'] = df['entry_time'].dt.strftime('%I %p')
            df['formatted_date'] = df['entry_time'].dt.strftime('%d %B')
            df['period_hours'] = pd.to_numeric(df['period_hours'], errors='coerce')
            df['period_hours'] = df['period_hours'].round(1).astype(str) + ' h'

            # Calculate the cutoff date for filtering
            cutoff_date = datetime.now() - timedelta(days=past_days)

            # Filter the DataFrame
            filtered_trades = df[
                (df['exit_time'] >= cutoff_date) &
                (df["strategy"] == strategy)
            ]

            df_sorted = filtered_trades.sort_values(by='period_hours', ascending=True)

            df_sorted = df_sorted[['trade_id', 'coin', 'side', 'period_hours', 'open_hour', 'formatted_date', 'trade_result']]

            # Check if the DataFrame is empty and send an appropriate message
            if df_sorted.empty:
                await update.message.reply_text("No trades match the specified criteria.")
            else:
                # Convert the DataFrame to a formatted string with custom separators and formatting
                formatted_rows = []
                for _, row in df_sorted.iterrows():
                    formatted_row = " | ".join(row.astype(str))
                    formatted_rows.append(formatted_row)
                message = "\n".join(formatted_rows)
                await update.message.reply_text(message)

                # Step 2: Group by date and calculate daily win percentage
                daily_win_percentage = df_sorted.groupby('formatted_date')['trade_result'].apply(lambda x: f"{(x == 'WIN').sum() / len(x) * 100:.1f}%").reset_index()

                # Step 3: Create a new DataFrame to store the daily win percentages
                daily_win_df = pd.DataFrame({
                    'Date': daily_win_percentage['formatted_date'],
                    'Win Percentage': daily_win_percentage['trade_result']
                })

                # Convert the daily_win_df DataFrame to a list of lists for tabulate
                table_data = daily_win_df.values.tolist()

                await update.message.reply_text(tabulate(table_data, tablefmt='plain'))

                # Calculate win rate
                df_sorted["Win Rate"] = df_sorted['trade_result'].apply(lambda result: 1 if result == "WIN" else 0)
                coin_stats = df_sorted.groupby('coin').agg({'Win Rate': 'mean', 'trade_result': 'count'})
                coin_stats.rename(columns={'Win Rate': 'Win Rate (%)', 'trade_result': 'Total Trades'}, inplace=True)
                coin_stats['Win Rate (%)'] = coin_stats['Win Rate (%)'] * 100

                # Convert the percentage string to a float for comparison
                coin_stats['Win Rate Float'] = coin_stats['Win Rate (%)'].astype(float)

                most_performant_coins = coin_stats[coin_stats['Win Rate Float'] >= 85.00].sort_values(by=['Win Rate Float', 'Total Trades'], ascending=[False, False])
                worst_performant_coins = coin_stats[coin_stats['Win Rate Float'] < 85.00].sort_values(by=['Win Rate Float', 'Total Trades'], ascending=[True, False])

                # Select the top and bottom n coins from each category
                top_n_most_performant_coins = most_performant_coins.head(n)
                top_n_worst_performant_coins = worst_performant_coins.head(n)

                # Format win rate as percentage without decimal places using .loc
                top_n_most_performant_coins.loc[:, 'Win Rate (%)'] = top_n_most_performant_coins['Win Rate (%)'].apply(lambda x: "{:.0f}%".format(x))
                top_n_worst_performant_coins.loc[:, 'Win Rate (%)'] = top_n_worst_performant_coins['Win Rate (%)'].apply(lambda x: "{:.0f}%".format(x))

                # Create the messages to send without headers and index label
                most_performant_message = "Most Performant Coins:\n" + top_n_most_performant_coins[['Win Rate (%)', 'Total Trades']].to_string(header=False)
                worst_performant_message = "Worst Performant Coins:\n" + top_n_worst_performant_coins[['Win Rate (%)', 'Total Trades']].to_string(header=False)

                # Send the messages
                await update.message.reply_text(most_performant_message)
                await update.message.reply_text(worst_performant_message)

                # Calculate win rate
                total_trades = len(df_sorted)
                win_trades = len(df_sorted[df_sorted['trade_result'] == "WIN"])
                win_rate = (win_trades / total_trades) * 100

                await update.message.reply_text(f"Total Trades: {total_trades}\nTotal Win Trades: {win_trades}\nTotal Win Rate: {win_rate:.2f}%")


    except ValueError:
        await update.message.reply_text("Invalid command format. Please use /strategytestpast-past_days-n-strategy format.")

async def fileselection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    files = os.listdir("./files/download/")
    reply_keyboard = [[file] for file in files]
    await update.message.reply_text(
        "List of available files. Choose a file to download:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECT_FILE

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        selected_file = update.message.text.strip()
        files_dir = "./files/download/"    
        file_path = os.path.join(files_dir, selected_file)
        chat_id = update.message.chat_id
        with open(file_path, 'rb') as file:
            await context.bot.send_document(chat_id=chat_id, document=file, reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await update.message.reply_text("Problem occured in uploading")

    return ConversationHandler.END

def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    update.message.reply_text("Download canceled.")
    return ConversationHandler.END


async def update_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    script_path = 'update_script.sh'
    try:
        subprocess.run(['bash', script_path], check=True)
        await update.message.reply_text("Version updated !")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Error executing script: {e}")


def telegram_handler() -> None:

    application = Application.builder().token(BOT_TOKEN_key).build()
    application.add_handler(CommandHandler("open", open_trades))
    application.add_handler(CommandHandler("update", update_script))
    application.add_handler(CommandHandler("tradepast", trade_past))
    application.add_handler(CommandHandler("coin", coin_stats))
    application.add_handler(CommandHandler("deletecoin", delete_coin))
    application.add_handler(CommandHandler("strategytestpast", strategy_test_past))
    download_handler = ConversationHandler(
    entry_points=[CommandHandler('download', fileselection)],
    states={
        SELECT_FILE: [MessageHandler(filters.TEXT, upload_file)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(download_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    telegram_handler()
