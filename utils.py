import pandas as pd

def load_data(path="./data/JOINProposals.xlsx"):
    df = pd.read_excel(path)
    translations = {'Unnamed: 0':"Index", 'publishDate':"publishDate", '網址':"url", '標題':"title", 
    '提議內容':"proposal",  '利益與影響':"benefits&impact", '附議數量':"#Votes", '附議門檻':"MinVotesNecessary", 
    '提送日期':"SubmissionDate", '關注數量':"Followers", '留言數量':"Messages", 'googleAnalytics':"GA",'提議者':"proposer" }
    df = df.rename(columns=translations)
    return df