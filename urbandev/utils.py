from typing import Literal
import pandas as pd
import json
import os
from sklearn.utils import Bunch
from datasets import Dataset, Features, Value, ClassLabel
import re
from googletrans import Translator


def load_data_excel(path="./data/JOIN_iVoting_Proposals_categorized.xlsx"):
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

def load_dataset(source: Literal['JOIN', 'iVoting']="JOIN", text_columns=['title', 'proposal'], language='en', type: Literal["sklearn", "huggingface", "pandas"]='sklearn'):
    sheets = {"JOIN": 0, "iVoting": 1}
    header = {"JOIN": 0, "iVoting": 1}
    #all_data = pd.read_excel('data/JOIN_iVoting_Proposals_categorized.xlsx', sheet_name=sheets[source], header=header[source])
    all_data = pd.read_excel('data/JoinData2025.xlsx', sheet_name=sheets[source], header=header[source])
    all_data['label'] = all_data['Category']
    if source == 'iVoting':
        all_data['date'] = pd.to_datetime(all_data['date'].apply(lambda x: x.split('-')[0]).apply(lambda x: x[:4] + '-' + x[4:6] + "-" + x[6:8] +" 00:00:00"))
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
    elif type == 'pandas':
        return all_data
    else:
        raise ValueError('style must be either sklearn, huggingface or pandas')


def load_bbc_dataset(text_columns=['title', 'text'], type: Literal["sklearn", "huggingface", "pandas"] = 'sklearn'):
    # Load the CSV file
    all_data = pd.read_csv("data/bbc_news_data.csv")  # Ensure the file path is correct

    # Convert category to labels
    all_data['label'] = all_data['category']  # Keeping it consistent with JOIN/iVoting

    # Create the final dataset structure
    training_dataset = pd.DataFrame({
        'text': all_data[text_columns].apply(lambda row: ' '.join(row.values.astype(str)), axis=1),
        'label': all_data['label']
    })

    # Return dataset in the requested format
    if type == 'sklearn':
        return training_dataset['text'].values, training_dataset['label'].astype('category').cat.codes
    elif type == 'huggingface':
        return Dataset.from_pandas(training_dataset, features=Features({
            'text': Value('string'),
            'label': ClassLabel(names=all_data['label'].unique().tolist())
        }))
    elif type == 'pandas':
        return all_data
    else:
        raise ValueError('Type must be either sklearn, huggingface, or pandas')



# Define the mapping from JSON keys to DataFrame column names
column_mapping = {
    "publishDate": "date",
    "網址": "link",
    "標題": "title_zh",
    "提議內容": "proposal_zh",
    "提議人": "proposer",  # Only if available in JSON
    "追蹤人數": "num_followers",  # Only if available in JSON
    "留言數": "num_comments",  # Only if available in JSON
    "提議內容_英": "proposal_en",  # Translated proposal
    "標題_英": "title_en"  # Translated title
}

def clean_text(text):
    """Remove illegal Excel characters from text."""
    if isinstance(text, str):
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    return text

def translate_text(text, translator):
    """Translate Traditional Chinese text to English."""
    if isinstance(text, str) and text.strip():
        try:
            return translator.translate(text, src='zh-TW', dest='en').text
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original if translation fails
    return text

def load_json(json_file):
    """Load JSON file and normalize it into a DataFrame."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert list of JSON objects to DataFrame
    df = pd.DataFrame(data)
    
    # Rename columns based on mapping
    df.rename(columns=column_mapping, inplace=True)
    
    # Ensure all expected columns exist
    for col in column_mapping.values():
        if col not in df:
            df[col] = None  # Fill missing columns with None
    
    # Clean all text fields
    df = df.applymap(clean_text)
    
    # Initialize translator
    translator = Translator()
    
    # Translate Chinese titles to English
    df["title_en"] = df["title_zh"].apply(lambda x: translate_text(x, translator))
    df["proposal_en"] = df["proposal_zh"].apply(lambda x: translate_text(x, translator))

    return df

if __name__=="__main__":
    load_dataset(source="iVoting", type='sklearn')

