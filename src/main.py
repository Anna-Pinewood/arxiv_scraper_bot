import datetime
from pathlib import Path
import pandas as pd
import yaml
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler, Application
from telegram import Update, Message, Bot
import logging

from scrape import scrape_arxiv


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Replace this with actual data or a function to fetch data from your DataFrame
# For demonstration purposes, I'll simulate a DataFrame
data = {
    'id': ['2205.00001', '2205.00002'],
    'title': ['A Comprehensive Overview of Large Language Models', 'Transformers in AI Applications'],
    'abstract': [
        'Large Language Models (LLMs) have recently demonstrated remarkable capabilities... This review article is intended to not only provide a systematic survey but also a quick comprehensive reference for the researchers.',
        'Transformers have revolutionized various AI tasks by effectively processing sequential data... Our work presents an extensive analysis of transformers and their impact on the field.'
    ],
    'created': ['11.05.2022', '10.05.2022'],
    'url': ['http://arxiv.org/abs/2205.00001', 'http://arxiv.org/abs/2205.00002']
}
df_articles = pd.DataFrame(data)


async def scrape(update: Update, context: CallbackContext):
    """E.g.
    /scrape llm,transformers 10 11.05 12.05
    """

    search_keywords = "llm,transformers,ai"  # Not used in this mock example
    start_date, end_date = "11.05", "11.05"  # Not used in this mock example

    search_keywords = context.args[0].split(',')
    num_articles, start_date, end_date = int(
        context.args[1]), context.args[2], context.args[3]
    def transform_date(
        x): return f"{datetime.date.today().year}-{int(x.split('.')[1]):02}-{int(x.split('.')[0]):02}"
    start_date = transform_date(start_date)
    end_date = transform_date(end_date)

    filters = {
        'abstract': search_keywords,
        'categories': ['cs.cl', 'cs.ai', 'cs.ro', 'cs.cv', 'cs.gt', 'cs.ne', 'cs.hc', 'cs.cy', 'cs.lg', 'cs.ir', 'cs.se', 'cs.ma']
    }
    print(f"date_from={start_date}, date_until={end_date}, filters={filters}")
    df_articles = scrape_arxiv(date_from=start_date,
                               date_until=end_date,
                               filters=filters,
                               )
    filtered_articles = df_articles[:num_articles]

    message = ""
    for i, row in filtered_articles.iterrows():
        article_id, title, abstract, created, url = row['id'], row[
            'title'], row['abstract'], row['created'], row['url']
        first_sentence = abstract.split(".")[0] + "."
        last_sentence = abstract.split(".")[-1].strip()
        message += f"{i+1}. {title}\nPublication date: {created}\nLink: {url}\nID: `{article_id}`\nAbstract: {first_sentence} ... {last_sentence}\n\n"

    await update.message.reply_text(message)


def get_abstract(update: Update, context: CallbackContext):
    article_id = context.args[0]  # Assuming the ID is passed as an argument

    # Find the article by ID
    article = df_articles[df_articles['id'] == article_id]
    if not article.empty:
        title, abstract, url = article[['title', 'abstract', 'url']].iloc[0]
        update.message.reply_text(
            f"{title}\nLink: {url}\n\nFull abstract:\n{abstract}")
    else:
        update.message.reply_text("Article not found.")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("get_abstract", get_abstract))
    application.add_handler(CommandHandler("scrape", scrape))
    # application.add_handler(MessageHandler(
    #     filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == '__main__':
    path_to_config = Path(__file__).parent.parent / 'config.yaml'
    with open(path_to_config, 'r') as file:
        config = yaml.safe_load(file)

    TELEGRAM_TOKEN = config['tg_token']

    main()
