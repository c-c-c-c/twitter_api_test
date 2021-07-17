from datetime import datetime
from datetime import timedelta
import requests
import os
import json
import Bearer
import pytz
import time
import pandas as pd

# 設定
query_params = {'query': '#鬼滅の刃無限列車編',
                'tweet.fields': "created_at,author_id,public_metrics", # スペースをいれない
                'max_results' : 500,
                "start_time":start_time ,
               "end_time": end_time,
               }

start_time_dt = make_local_dt(datetime(2020, 10, 16, 0, 0, 0) )
search_url = "https://api.twitter.com/2/tweets/search/all"

def main():

    movie_name = str(start_time_dt.date())+"_"+"鬼滅の刃"

    # 終了日
    end_time_dt = start_time_dt + timedelta(days=88) # 2020年10月16日スタート

    start_time = dt2localiso(start_time_dt)
    end_time = dt2localiso(end_time_dt)

    # To set your environment variables in your terminal run the following line:
    # export 'BEARER_TOKEN'='<your_bearer_token>'
    bearer_token = Bearer.BEARER
    
    json_response = None
    query_params.pop("until_id", None)
    tweet_data = []

    for query_no in range(1,100000):
        time.sleep(5) # 連続するとエラーになる
        if json_response:
            print(query_no)
            query_params.pop("start_time", None)
            query_params.pop("end_time", None)
            query_params["until_id"] = int(json_response["data"][-1]["id"])
            
            print(query_params["until_id"])
        
        
        json_response = connect_to_endpoint(search_url, 
                                        create_headers(bearer_token), # headerを作る
                                        query_params,
                                        )
        for i,tmp_content in enumerate(json_response["data"]):
            
            # 置き換える日本時間に
            tmp_content["created_at"] = iso_to_localdt(tmp_content["created_at"])
            
            try:
                tweet_data.append([tmp_content["id"], 
                                tmp_content["created_at"], tmp_content["text"].replace('\n',''),
                                tmp_content["public_metrics"]["like_count"],
                                tmp_content["public_metrics"]["retweet_count"], 
                                tmp_content["author_id"] ])
            except Exception as e:
                print(e)
            if tmp_content["created_at"] < start_time_dt :
                # この３行を入れないと、最後の部分が取れない
                df = pd.DataFrame(tweet_data, columns = ["tweet_id", "date","text","like","retweet", "author_id"])
                df = df.set_index("tweet_id")
                df.to_csv("./data/"+ movie_name +"_last.csv")
                break
            
        if query_no % 40 == 0: # 40クエリごとに書き出し(50万件)
            df = pd.DataFrame(tweet_data, columns = ["tweet_id", "date","text","like","retweet", "author_id"])
            df = df.set_index("tweet_id")
            df.to_csv("./data/"+ movie_name +"_"+str(query_no) +".csv")
            tweet_data = [] # 空にする
        
        if tmp_content["created_at"] < start_time_dt :
            break


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

def connect_to_endpoint(url, headers, params):
    response = requests.request("GET", search_url, headers=headers, params=params)
    print("response_st",response.status_code)
    if response.status_code != 200:
        raise Exception("response_st",response.status_code, response.text)
    return response.json()

# 時刻を変換する関数

def make_local_dt (dt):
    utc_dt = dt - timedelta(hours=+9)
    return (pytz.utc.localize(utc_dt).astimezone(pytz.timezone("Asia/Tokyo")) )

    
def dt2localiso(dt):
    # この段階で
    if dt is None:
        return ''
    
    return dt.isoformat()

def iso_to_localdt(iso_str):
    dt = None
    try:
        dt = datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        dt = pytz.utc.localize(dt).astimezone(pytz.timezone("Asia/Tokyo"))
    except ValueError:
        try:
            dt = datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            dt = dt.astimezone(pytz.timezone("Asia/Tokyo"))
        except ValueError:
            pass
    return dt


main()

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields



        