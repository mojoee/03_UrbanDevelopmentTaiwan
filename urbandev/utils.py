from typing import Literal
import pandas as pd
import os
from sklearn.utils import Bunch
from datasets import Dataset, Features, Value, ClassLabel

def load_data_excel(path="./data/JOINProposals.xlsx"):
    df = pd.read_excel(path)
    translations = {'Unnamed: 0':"Index", 'publishDate':"publishDate", '網址':"url", '標題':"title", 
    '提議內容':"proposal",  '利益與影響':"benefits&impact", '附議數量':"#Votes", '附議門檻':"MinVotesNecessary", 
    '提送日期':"SubmissionDate", '關注數量':"Followers", '留言數量':"Messages", 'googleAnalytics':"GA",'提議者':"proposer" }
    df = df.rename(columns=translations)
    return df


def load_data_csv(path="./data/JOINProposals.xlsx"):
    df = pd.read_csv(path)
    translations = {'Unnamed: 0':"Index", 'publishDate':"publishDate", '網址':"url", '標題':"title", 
    '提議內容':"proposal",  '利益與影響':"benefits&impact", '附議數量':"#Votes", '附議門檻':"MinVotesNecessary", 
    '提送日期':"SubmissionDate", '關注數量':"Followers", '留言數量':"Messages", 'googleAnalytics':"GA",'提議者':"proposer" }
    df = df.rename(columns=translations)
    return df


def save_data(df, path="./data/translatedJoinProposals.csv"):
    destination, file = os.path.split(path)
    os.makedirs(destination, exist_ok=True)
    df.to_csv(path, index=False)
    

def clean_data(df):
    return df

def load_dataset(sources=['JOIN Proposals', 'iVoting Proposals'], text_columns=['title', 'proposal'], language='en', type: Literal["sklearn", "huggingface"]='sklearn'):
    all_data = pd.read_excel('data/JOIN_iVoting_Proposals_categorized.xlsx')
    all_data['label'] = all_data['Category']
    training_dataset = pd.DataFrame(data={
        'text': all_data[[column + '_' + language for column in text_columns]].apply(lambda row: '_'.join(row.values.astype(str)), axis=1),
        'label': all_data['Category'],
        'date': all_data['date']
    })
    # check for int in text column
    if type == 'sklearn':
        return training_dataset['text'].values, training_dataset['label'].astype('category').cat.codes, training_dataset['date'].values
    elif type == 'huggingface':
        return Dataset.from_pandas(training_dataset, features=Features({'text': Value('string'), 'label': ClassLabel(names=all_data['Category'].unique().tolist())}))
    else:
        raise ValueError('style must be either sklearn or huggingface')

load_dataset(type='sklearn')

