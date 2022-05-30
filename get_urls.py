import pandas as pd
import re
import string
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from database import engine


def clean_text(text):
    '''clean text of miscellaneous punctuation and characters'''
    text = text.lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('\w*\d\w*', '', text)
    text = re.sub('[‘’“”…]', '', text)
    text = re.sub('\n', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('/(\s\s\s*)/g', ' ', text)
    return text


def clean_search_input(input_str):
    '''Cleans search input and returns an '&' delimitted string for tsquery'''
    input_str = clean_text(input_str)
    clean_search = input_str.lower().replace(' ', '&')
    return clean_search


def define_query(search_input):
    '''Defines the query to be sent to the database'''

    bigger_query = f'''select
	total_vids."videoID",
	complete_videos.title,
	complete_videos."channelID",
	total_vids.views_count,
	total_vids.likes,
	total_vids.comments_,
	total_vids.length_,
	total_vids.like_ratios,
	total_vids.comment_ratio,
	total_vids.polarity,
	total_vids.subjectivity
	from
		total_vids
	left join complete_videos on
		total_vids."videoID" = complete_videos."videoID"
	where total_vids."videoID" in (
	select "videoID" from complete_videos 
	where to_tsvector(title) @@ to_tsquery('{clean_search_input(search_input)}'))'''
    return bigger_query


def get_top_six(input_query='Python'):
    '''Takes in a dataframe of results from a query, performs PCA, and returns the top 6 highest PCA scored video IDs'''
    try:
        sql_query = define_query(input_query)

        stats_table = pd.read_sql(text(sql_query), con=engine)
        # PCA
        features = ['views_count', 'likes', 'comments_',
                    'like_ratios', 'comment_ratio', 'polarity', 'subjectivity']
        # Separating out the features
        x = stats_table.loc[:, features].values
        # Standardizing the features
        x = StandardScaler().fit_transform(x)
        pca = PCA(n_components=1)
        principalComponents = pca.fit_transform(x)
        principalDf = pd.DataFrame(data=principalComponents, columns=['PC1'])
        finalDf = pd.concat([stats_table[['videoID', 'title', 'channelID']],
                            principalDf], axis=1).sort_values(by='PC1', ascending=False)
        try:
            id_list = finalDf['videoID'].head(6).to_list()
        except:
            id_list = finalDf['videoID'].to_list()
    except:
        id_list = ['VOyg2LzNiOA', 'sCddrLwH-fc', '7rAOLvHX_-8',
                   'Z9amZgbxhaI', 'KJgtrEGYsTo', 'kqtD5dpn9C8']
    return id_list


if __name__ == "__main__":
    search_string = 'How to play the guitar'
    print(f'Searching for: {search_string}')
    results = get_top_six(search_string)
    print(results)
