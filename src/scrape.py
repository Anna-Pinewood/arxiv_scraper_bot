import logging
import arxivscraper.arxivscraper as ax
import pandas as pd
logger = logging.getLogger(__name__)


def scrape_arxiv(date_from: str,
                 date_until: str | None = None,
                 filters: dict[str, list[str]] | None = None
                 ) -> pd.DataFrame:
    if date_until is None:
        date_until = str(pd.Timestamp.today().date())
    scraper = ax.Scraper(category='cs',
                         date_from=date_from,
                         date_until=date_until,
                         t=10,
                         filters=filters)
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

    filtered_df = filtered_df[filtered_df['categories'].apply(
        lambda x:  len(set(x.split()) & set(filters['categories'])) > 0)]
    logger.info("Articles left after cat filering: %s", len(filtered_df))

    print(filtered_df.columns)
    filtered_df = filtered_df[filtered_df['abstract'].apply(
        lambda abstract:  len(set(abstract.split()) & set(filters['abstract'])) > 0)]

    # filtered_df = filtered_df.abstract.str.contains(pattern, regex=True)
    logger.info("Articles left after abstract filering: %s", len(filtered_df))

    filtered_df = filtered_df.sort_values(by='created', ascending=True)
    filtered_df.sort_values(by='created', ascending=False)
    filtered_df['created'] = filtered_df['created'].dt.strftime('%Y-%m-%d')
    filtered_df = filtered_df.reset_index(drop=True)
    return filtered_df
