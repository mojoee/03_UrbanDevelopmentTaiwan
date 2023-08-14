import pandas as pd
from urbandev.utils import save_data

path1 = "./data/translatedJoinProposals.csv"
path2 = "./data/translatedJoinProposalsTitles.csv"
outputfile = "./data/translatedJoinProposalsCombined.csv"
df1 = pd.read_csv(path1)
df2 = pd.read_csv(path2)

print(df2.columns)
df1["titleEN"] = df2["titleEN"]
save_data(df1, outputfile)
