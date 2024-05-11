from datetime import time
import logging
import re
from urllib.request import urlopen
from urllib.error import HTTPError
from xml.dom import minidom
import arxivscraper.arxivscraper as ax
import pandas as pd
logger = logging.getLogger(__name__)


def scrape_arxiv(date_from: str,
                 date_until: str | None = None,
                 filters: dict[str, list[str]] | None = None,
                 filter_regex: str | None = None
                 ) -> pd.DataFrame:
    if date_until is None:
        date_until = str(pd.Timestamp.today().date())
    scraper = ax.Scraper(category='cs',
                         date_from=date_from,
                         date_until=date_until,
                         t=10)
    #  filters=filters)
    output = scraper.scrape()
    logger.info("Scraped %s articles", len(output))

    cols = ('id', 'title', 'categories', 'abstract',
            'created', 'updated', 'authors', 'url')
    df = pd.DataFrame(output, columns=cols)

    # filtered_df['updated'] = pd.to_datetime(filtered_df['updated'])
    df['created'] = pd.to_datetime(df['created'])
    # filtered_df = filtered_df[ (filtered_df.updated < date_to) & (filtered_df.updated > date_from) | (filtered_df.created < date_to) & (filtered_df.created > date_from)]
    filtered_df = df[(df.created < date_until)
                     & (df.created > date_from)]
    logger.info("Articles left after date filering: %s", len(filtered_df))

    if 'categories' in filters:
        filtered_df = filtered_df[filtered_df['categories'].apply(
            lambda x:  len(set(x.split()) & set(filters['categories'])) > 0)]
        logger.info("Articles left after cat filering: %s", len(filtered_df))

    filtered_df = filtered_df[filtered_df['abstract'].str.contains(
        filter_regex, regex=True)]
    logger.info("Articles left after abstract filering: %s", len(filtered_df))

    filtered_df = filtered_df.sort_values(by='created', ascending=True)
    filtered_df.sort_values(by='created', ascending=False)
    filtered_df['created'] = filtered_df['created'].dt.strftime('%Y-%m-%d')
    filtered_df = filtered_df.reset_index(drop=True)
    return filtered_df


def scrape_abstract(article_id: str) -> dict[str, str]:
    logger.info("Fetching article %s", article_id)
    k = 5
    while k > 0:
        try:
            usock = urlopen(
                'http://export.arxiv.org/api/query?id_list='+article_id)
            xmldoc = minidom.parse(usock)
            usock.close()
            break
        except HTTPError as e:
            if e.code == 503:
                to = int(e.hdrs.get("retry-after", 30))
                print("Got 503. Retrying after 10 seconds.")
                time.sleep(10)
                k -= 1
                continue
            else:
                raise
    if k == 0:
        return -1

    d = xmldoc.getElementsByTagName("entry")[0]
    abstract = d.getElementsByTagName(
        "summary")[0].firstChild.data.strip()
    abstract = process_newlines_abstract(abstract)

    title = d.getElementsByTagName(
        "title")[0].firstChild.data.replace("\n", " ")
    published = d.getElementsByTagName("published")[0].firstChild.data
    url = f"http://www.arxiv.org/abs/{article_id}"
    return {'abstract': abstract, 'title': title,
            'published': published, 'url': url}


def process_newlines_abstract(input_string):
    output_string = ""
    for i in range(len(input_string)):
        if input_string[i] == "\n":
            if i > 0 and input_string[i-1] == ".":
                output_string += "\n"
        else:
            output_string += input_string[i]
    output_string = output_string.replace("\n", "\n\n")
    return output_string
