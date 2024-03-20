import pandas
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
import sqlite3

sqliteConnection = sqlite3.connect('smartAggie.sqlite')

def comments_sentiment(comment:str) ->dict:
    """

    :param comment: str comment to analyze
    :return: tuple with sentimewnt scores
    """
    sentiment_analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = sentiment_analyzer.polarity_scores(comment)
    return sentiment_dict


def comment_processor(prof:str) ->dict:
    """

    :param prof: prof name's comments to analyze
    :return: tuple with sentimewnt scores
    """
    comments_df = pandas.read_sql(sql=f"select * from Comments where \"Name\" = \"{prof}\";",
                                      con=sqliteConnection)
    grouped_df = comments_df.groupby("Name")["Comment"]
    prof_sentiment_dict ={}
    for name,group in grouped_df:
        comment_aggregated =' '.join(group.values)
        prof_sentiment_dict= comments_sentiment(comment=comment_aggregated)
    return prof_sentiment_dict



comment_processor()
