from urbandev.nlp import zero_shot_classification
from urbandev.utils import load_data_csv, load_data_excel


data = load_data_excel("./data/JOIN_iVoting_Proposals_categorized.xlsx")
df = load_data_csv('./data/translatedJoinProposals.csv')

labels = ['Transport', 'Law & Justice', 'Education', 'Finance', 'Environment & Climate', 'Energy', 'Social', 'Military and National Security']
zero_shot_classification(df.iloc[2]["titleEN"], labels)