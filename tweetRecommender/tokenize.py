from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from tweetRecommender.mongo import mongo
from tweetRecommender import tweetfilter
from tweetRecommender.stopwords import stopwords as stopwords_extension
import functools32

ps = PorterStemmer()

@functools32.lru_cache()
def get_stopwords():
    stops = stopwords.words('english')
    stops.extend(["'re", "n't", "'s"])
    stops.extend(stopwords_extension)
    return stops

def get_terms(text):
    return list(set(tokenize(text)))

@functools32.lru_cache()
def tokenize(text):
    text = tweetfilter.clean_tweet(text)
    return [ps.stem(w) for w in word_tokenize(text)
            if not w in get_stopwords()]

@functools32.lru_cache()
def tokenize_diversity(text):
    text = tweetfilter.clean_tweet_hashtag(text)
    return [ps.stem(w) for w in word_tokenize(text)
            if not w in get_stopwords()]

def handle(tweet, bulk):
    text = tweet["text"]
    tweet_id = tweet["_id"]
    tokens = list(set(tokenize(text.encode("utf-8"))))
    bulk.find({'_id': tweet_id}).update({'$set': {'terms': tokens}})

if __name__ == '__main__':
    bulk = mongo.db.sample_tweets.initialize_unordered_bulk_op()
    for tweet in mongo.db.sample_tweets.find():
        handle(tweet, bulk)
    bulk.execute()
