print("test")
function get_absolute_time(webpage_creation_time, tweet_creation_time) {
  return Math.abs(webpage_creation_time - tweet_creation_time)
}

function get_relative_time(webpage_creation_time, tweet_creation_time) {
  return tweet_creation_time - webpage_creation_time
}

function get_binary_time_decision(webpage_creation_time, tweet_creation_time) {
  // webpage published... (-1: before, 1: after)
  if ((tweet_creation_time - webpage_creation_time) >= 0)
    return 1
  return -1
}

function get_capped_time(webpage_creation_time, tweet_creation_time) {
  // return 0 for all tweets published before webpage and real value for other
  if ((tweet_creation_time - webpage_creation_time) > 0)
    return (tweet_creation_time - webpage_creation_time)
  return 0
}

function get_time_values(query_url, tweet_creation_time) {
  webpage_creation_time = db.sample_webpages.find({url: query_url}).limit(1).next().created_at
  time_values = {}
  time_values.absolute_time_difference = get_absolute_time(webpage_creation_time, tweet_creation_time)
  time_values.relative_time_difference = get_relative_time(webpage_creation_time, tweet_creation_time)
  time_values.binary_decision = get_binary_time_decision(webpage_creation_time, tweet_creation_time) 
  time_values.capped_time_after = get_capped_time(webpage_creation_time, tweet_creation_time)
  return time_values
}

db.evaluation_cache_fresh.find().forEach(function(cachedResult){
  print("starting " + cachedResult.query_url + " with " + cachedResult.tweet_list.length + "tweets")
  cachedResult.tweet_list.forEach(function(tweet){
    /* Only needs to be done once per tweet */
    var complete_tweet_data = db.sample_tweets.findOne({
      tweet_id: tweet.tweet.tweet_id
    },{
      hashtags: 1,
      full_urls: 1
    });
    var user = db.sample_tweets.findOne({
      "user.screen_name": tweet.tweet.user.screen_name
    }).user;
    var times = get_time_values(cachedResult.query_url, tweet.tweet.created_at);
    var contains_url = (complete_tweet_data.full_urls.indexOf(cachedResult.query_url) == -1) ? false : true

    var count = db.evaluation.find({webpage: cachedResult.query_url, tweet:tweet.tweet._id + ""}).count()
    print(count + " tweet_id: " + tweet.tweet._id)
    db.evaluation.find({webpage: cachedResult.query_url, tweet:tweet.tweet._id + ""}).forEach(function(evaluation){
      evaluation.scores = {}
      evaluation.scores.lda_cossim = tweet.scores[0].lda_cossim
      evaluation.scores.language_model = tweet.scores[1].language_model
      evaluation.tweet_length = tweet.tweet.terms.length // number of terms after stopword removal and stemming
      evaluation.chars = tweet.tweet.text.length
      evaluation.isverified = user.verified
      evaluation.followers_count = user.followers_count
      evaluation.statuses_count = user.statuses_count
      evaluation.listed_count = user.listed_count
      evaluation.friends_count = user.friends_count
      evaluation.userid = user.user_id
      evaluation.times = times
      evaluation.contains_url = contains_url
      evaluation.url_count = complete_tweet_data.full_urls.length
      evaluation.hashtag_count = complete_tweet_data.hashtags.length
      db.evaluation_enriched.save(evaluation)
    });
  });
});

