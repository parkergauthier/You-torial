import os
import pandas as pd
import json
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy import values
from metrics import get_metrics, extract_metrics
from comments_request import get_comments, clean_comments

# Connecting to DB
conn_DB = #"redacted"
db = create_engine(conn_DB)
conn = db.connect()


# Setting Paths
API_BASE_DIR = "scraping"
API_KEY_PATH = os.path.join(API_BASE_DIR, "api_keys.json")
JSON_PATH_IN = os.path.join(API_BASE_DIR, "500_videos.json")
OUT_PATH_TEST = os.path.join(API_BASE_DIR, "testing.csv")

# Reading API Key
with open(API_KEY_PATH, "r") as f:
    api_keys = json.load(f)
api_key = api_keys["Amal_key"]

# Reading in sample JSON, to be changed with real video list later
####################
# with open(JSON_PATH_IN, "r") as f:
#     videos = json.load(f)

# create connection for query purpose
conn_query = psycopg2.connect(
    dbname="redacted",
    user="redacted",
    host="redcated",
    password="redacted",
)

cur = conn_query.cursor()


def snowball(videos_num=100):

    cur.execute(f"select * from no_repeat_ids limit {videos_num}")
    i = 0
    for video in cur:
        i += 1
        # try:
        video_id = send2sql([video[0]])
        print(f"{i} videos completed: {video_id[0]}")
        # except:
        #print(f"PASSED ON THIS ONE: {video[0]} ")
        if i == videos_num:
            print("YAY! ALL DONE! :D")


def send2sql(videos_list):
    """Looping through videos from list to get metrics/comments and pushing them to sql"""
    for i in videos_list:

        # grabbing metrics
        metrics_dict_dirty = get_metrics(i, apiKey=api_key)
        try:
            metrics_dict = extract_metrics(metrics_dict_dirty)
        except:
            print(
                f"This video: [{videos_list[0]}] is unavalable, and has been coded with -9 in metrics"
            )
            metrics_dict = {
                "videoID": videos_list[0],
                "likes": -9,
                "comments": -9,
                "length": -9,
                "views": -9,
            }
        # creating df for metrics
        df_met = pd.Series(metrics_dict).to_frame().T

        # sending df to SQL
        df_met.to_sql(con=conn, name="youtube_metrics", if_exists="append")

        # grabbing comments
        try:
            comments_dicts = get_comments(i, apiKey=api_key)
            clean_comments_list = clean_comments(comments_dicts)
        except:
            clean_comments_list = []

        # Creating df for comments
        video_string = [i] * len(clean_comments_list)
        df_comm = pd.DataFrame(
            list(zip(video_string, clean_comments_list)), columns=["videoID", "comment"]
        )

        # Sending df to SQL
        df_comm.to_sql(con=conn, name="youtube_comments", if_exists="append")

    return videos_list


if __name__ == "__main__":
    snowball(10)
