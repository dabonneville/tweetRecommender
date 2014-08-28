#!/bin/sh

mongoexport --host 172.16.22.219 -u mpss14n -p twitter -d twitter_subset -c evaluation_enriched --csv --fields webpage,rating,tweet,uid,scores.lda_cossim,scores.language_model,tweet_length,chars,isverified,followers_count,statuses_count,listed_count,friends_count,times.absolute_time_difference,times.relative_time_difference,times.binary_decision,times.capped_time_after,contains_url,url_count,hashtag_count > `dirname $0`/../dump/twitter_subset/evaluationEnriched2.csv