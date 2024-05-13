import datetime
from pathlib import Path
import pandas as pd
import yaml
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler, Application
from telegram import Update, Message, Bot
import logging

from scrape import scrape_abstract, scrape_arxiv


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape(update: Update, context: CallbackContext):
    """E.g.
    /scrape llm|transformers|large_language_models 10 11.05 12.05
    """
    if len(context.args) < 4:
        msg = "Your command missing some args. Use /help for instructions."
        await update.message.reply_text(msg)
    regex_keywords = context.args[0].replace("_", " ")
    search_keywords = context.args[0].replace('&', '|').split('|')

    num_articles, start_date, end_date = int(
        context.args[1]), context.args[2], context.args[3]

    def transform_date(
        x): return f"{datetime.date.today().year}-{int(x.split('.')[1]):02}-{int(x.split('.')[0]):02}"
    start_date = transform_date(start_date)
    end_date = transform_date(end_date)

    filters_for_arxiv_lib = {
        'abstract': search_keywords,
        # 'categories': ['cs.cl', 'cs.ai', 'cs.ro', 'cs.cv', 'cs.gt', 'cs.ne', 'cs.hc', 'cs.cy', 'cs.lg', 'cs.ir', 'cs.se', 'cs.ma']
        # 'categories': ['cs.cl']
    }

    df_articles = scrape_arxiv(date_from=start_date,
                               date_until=end_date,
                               filters=filters_for_arxiv_lib,
                               filter_regex=regex_keywords,
                               )
    if len(df_articles) == 0:
        message = "No articles for this query. Perhaps try broaden search dates?"
        await update.message.reply_text(message, parse_mode="HTML")

    filtered_articles = df_articles[:num_articles]

    message = ""
    for i, row in filtered_articles.iterrows():
        article_id, title, abstract, created, url = row['id'], row[
            'title'].capitalize(), row['abstract'], row['created'], row['url']
        first_sentence = (abstract.split(".")[0] + ".").capitalize()
        last_sentence = (abstract.split(".")[-1].strip()).capitalize()
        if last_sentence == '':
            last_sentence = abstract.split(".")[-2].strip().capitalize()

        message += f"{i+1}. <b>{title}</b>\nPublication date: <u>{created}</u>\nLink: {url}\nID: <code>{article_id}</code>\nAbstract:\n<blockquote>{first_sentence} ... {last_sentence}</blockquote>\n\n"

        if (i + 1) % 5 == 0 or i == len(filtered_articles) - 1:
            await update.message.reply_text(message, parse_mode="HTML")
            message = ""


async def get_abstract(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        msg = "Your command missing article_id. Use /help for instructions."
        await update.message.reply_text(msg)
    article_id = context.args[0]

    article_info = scrape_abstract(article_id)
    if article_info == 1:
        await update.message.reply_text("Article not found.")

    title, abstract, published, url = article_info['title'], article_info[
        'abstract'], article_info['published'], article_info['url']
    await update.message.reply_text(
        f"<b>{title}</b>\nLink: {url}\nDate: <u>{published}</u>\nFull abstract:\n<blockquote>{abstract}</blockquote>", parse_mode="HTML")


help_message = f"""
Hello, this is <b>Arxiv Scraper Bot</b>! Get latest articles on interested topics right here!

====Command examples====:
<code>/scrape</code>
<code>/scrape llm|transformers&robots 10 08.05 12.05</code>
<code>/scrape dwh 10 08.05 12.05</code>
<code>/scrape llm|llms 10 {(pd.Timestamp.today() - pd.Timedelta(days=3)).date().strftime("%d.%m")} {pd.Timestamp.today().date().strftime("%d.%m")}</code> \
    – <b>scrape latest articles for 3 days</b>
That means
/scrape llm|transformers&robots <code>n_articles=10</code>, publish date is between 08.05 to 12.05 of current year.
This command will get you last 10 articles, abctract of which containt either llm substring or both transformers and robots. Search is case insensitive.

Mind that if you want to use spaces, use <code>_</code>. Simple space won't work <code>/scrape "large language models|cats" 10 08.05 12.05</code> - this won' work.\
 But <code>/scrape "large_language_models|cats" 10 08.05 12.05</code> will work.
 
Note that search is in predefiened category - computer science.
<b>Scraping can take a while, e.g., scraping for last 3 days will take approximarely <u>30 seconds</u></b>.

<code>/get_abstract</code>
<code>/get_abstract 2405.05955</code>
This command will get ypu abstract of the article with arxiv id passed. You can copy arxiv id from /scrape command output.
"""


async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(help_message,  parse_mode="HTML")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("start", help))
    application.add_handler(CommandHandler("get_abstract", get_abstract))
    application.add_handler(CommandHandler("scrape", scrape))

    application.run_polling()


if __name__ == '__main__':
    path_to_config = Path(__file__).parent.parent / 'config.yaml'
    with open(path_to_config, 'r') as file:
        config = yaml.safe_load(file)

    TELEGRAM_TOKEN = config['tg_token']

    main()
