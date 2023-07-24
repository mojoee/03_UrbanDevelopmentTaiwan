from googletrans import Translator
from urbandev.utils import load_data_excel, save_data
import re

def clean_proposals(df):
    pass

def translate_text(text):
    try:
        translation = translator.translate(text, src="zh-tw", dest="en").text
    except Exception as e:
        print("Exception occured:", e)
        translation = "Could not translate"
    return translation

if __name__ == "__main__":
    df = load_data_excel("./data/JOINProposals.xlsx")
    translator = Translator()
    #df["titleEN"] = df["title"].apply(lambda x: translator.translate(x, src="zh-tw", dest="en").text)
    
    df["proposal"] = df["proposal"].apply(lambda x: str(x).replace('\n', ''))
    df["proposal"] = df["proposal"].apply(lambda x: str(x).replace('\xa0', ''))
    for index, row in df.iterrows():
        if not re.findall(r'[\u4e00-\u9fff]+', str(row["proposal"])):
            print(row["proposal"])
            df.at[index, "proposal"] = "沒有提供上下文"
    df["proposalEN"] = df["proposal"].apply(lambda x: translate_text(x))
    df["titleEN"] = df["title"].apply(lambda x: translate_text(x))
    print(df.head())
    save_data(df)
