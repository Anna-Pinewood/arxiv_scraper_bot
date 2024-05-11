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
    /scrape llm|transformers&robots 10 11.05 12.05
    """

    regex_keywords = context.args[0]
    search_keywords = context.args[0].replace('&', '|').split('|')

    num_articles, start_date, end_date = int(
        context.args[1]), context.args[2], context.args[3]
    def transform_date(
        x): return f"{datetime.date.today().year}-{int(x.split('.')[1]):02}-{int(x.split('.')[0]):02}"
    start_date = transform_date(start_date)
    end_date = transform_date(end_date)

    filters_for_arxiv_lib = {
        'abstract': search_keywords,
        'categories': ['cs.cl', 'cs.ai', 'cs.ro', 'cs.cv', 'cs.gt', 'cs.ne', 'cs.hc', 'cs.cy', 'cs.lg', 'cs.ir', 'cs.se', 'cs.ma']
        # 'categories': ['cs.cl']
    }
    print(
        f"date_from={start_date}, date_until={end_date}, filters={filters_for_arxiv_lib}")
    df_articles = scrape_arxiv(date_from=start_date,
                               date_until=end_date,
                               filters=filters_for_arxiv_lib,
                               filter_regex=regex_keywords,
                               )
    filtered_articles = df_articles[:num_articles]

    message = ""
    for i, row in filtered_articles.iterrows():
        article_id, title, abstract, created, url = row['id'], row[
            'title'].capitalize(), row['abstract'], row['created'], row['url']
        first_sentence = (abstract.split(".")[0] + ".").capitalize()
        last_sentence = (abstract.split(".")[-1].strip()).capitalize()
        if last_sentence == '':
            last_sentence = abstract.split(".")[-2].strip()

        message += f"{i+1}. <b>{title}</b>\nPublication date: <u>{created}</u>\nLink: {url}\nID: <code>{article_id}</code>\nAbstract:\n<blockquote>{first_sentence} ... {last_sentence}</blockquote>\n\n"

        if (i + 1) % 5 == 0 or i == len(filtered_articles) - 1:
            await update.message.reply_text(message, parse_mode="HTML")
            message = ""


async def get_abstract(update: Update, context: CallbackContext):
    article_id = context.args[0]

    article_info = scrape_abstract(article_id)
    if article_info == 1:
        await update.message.reply_text("Article not found.")

    title, abstract, published, url = article_info['title'], article_info[
        'abstract'], article_info['published'], article_info['url']
    await update.message.reply_text(
        f"<b>{title}</b>\nLink: {url}\nDate: <u>{published}</u>\nFull abstract:\n<blockquote>{abstract}</blockquote>", parse_mode="HTML")


help_message = """
command options:
`/scrape llm|transformers&robots 10 08.05 12.05`
"""


async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Я бот с кнопками реакции.')


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("get_abstract", get_abstract))
    application.add_handler(CommandHandler("scrape", scrape))

    application.run_polling()


if __name__ == '__main__':
    path_to_config = Path(__file__).parent.parent / 'config.yaml'
    with open(path_to_config, 'r') as file:
        config = yaml.safe_load(file)

    TELEGRAM_TOKEN = config['tg_token']

    main()
