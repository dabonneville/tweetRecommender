from __future__ import division 
from tweetRecommender.mongo import mongo
from tweetRecommender.query import run
from bson import ObjectId
import functools32
import sys

TWEETS_COLLECTION = 'tweets'
WEBPAGES_COLLECTION = 'webpages'
TWEETS_SUBSAMPLE = 'sample_tweets'
WEBPAGES_SUBSAMPLE = 'sample_webpages'

EVALUATION_GATHERER = "terms"
EVALUATION_FILTERS = []
EVALUATION_RANKERS = ['lda_cossim', 'language_model', 'adaboost', 'logistic_regression']
CACHED_RESULTS_COLLECTION = 'evaluation_cache_fresh'

@functools32.lru_cache()
def get_evaluated_collection(url):
    value = []
    collection = mongo.coll("evaluation").aggregate([{"$match" : { "webpage" : url}},
                                               {"$group": {
        "_id": "$tweet",
        "positive": {"$sum": {"$cond": {"if": {"$eq": ["$rating", +1]}, "then": 1, "else": 0}}},
        "negative": {"$sum": {"$cond": {"if": {"$eq": ["$rating", -1]}, "then": 1, "else": 0}}},
    }}])["result"]
    for tweet in collection:
        if tweet["positive"] > tweet["negative"]:
            value.append(ObjectId(tweet["_id"]))
    return set(value)    

def calculate_MAP(query_url):    
    collections = get_evaluated_collection(query_url)                        
    map_dict = dict()                
    for ranker in EVALUATION_RANKERS:                
        relevants = 0
        position = 0 
        precisions = []
        rankers = ranker.split(',')
        ranker_result = run(url=query_url, gatherer=EVALUATION_GATHERER, rankers=rankers,
                            filters=EVALUATION_FILTERS, fields=['user.screen_name', 'created_at', 'text'],
                            tweets_ref=TWEETS_SUBSAMPLE, webpages_ref=WEBPAGES_SUBSAMPLE, limit = None)                    
        for _, tweet in ranker_result:
            position += 1                    
            if (ObjectId(tweet["_id"]) in collections):                                
                relevants += 1
                precisions.append(relevants/position)
        if relevants == 0:
            meanap = 0
        else:
            meanap = sum(precisions)/relevants
        map_dict[ranker] = meanap                                                                           
    mongo.coll(CACHED_RESULTS_COLLECTION).update({"query_url":query_url},{"$set": { "eval.map" : map_dict }})
    return map_dict

def evaluate_collections():
    rank_map = dict()  
    count = 0
    for webpage in mongo.coll(CACHED_RESULTS_COLLECTION).find({},{"query_url":1}):                     
        count += 1        
        value = 0                                
        sys.stdout.write("\nevaluated article: %s\n" % count)
        ranks_dict = calculate_MAP(webpage["query_url"])                                    
        for key in ranks_dict.keys():
            sys.stdout.write("AP %s : %f\n" % (key,ranks_dict[key]))                        
            if key in rank_map:
                value = rank_map.get(key)
            rank_map[key] = ranks_dict[key] + value                
    sys.stdout.write("\n")                                                                                                
    for ranker in EVALUATION_RANKERS:        
        sys.stdout.write("Average MAP %s : %f\n" % (ranker, (rank_map[ranker]/count)))
    sys.stdout.flush()
                      
if __name__ == '__main__':
    evaluate_collections()         
