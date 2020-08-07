import numpy as np 
import pandas as pd 
import os 
#set up working directory 
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

#DATA
main = pd.read_csv("output/grant_grant.csv")
main["pubdate"] = main["pubdate"].astype(float)
main = main.drop("Unnamed: 0", axis = 1)
cites = pd.read_csv("output/grant_cite.csv")
cites = cites.drop("Unnamed: 0", axis = 1)
firmnum = pd.read_csv("output/grant_firm.csv")
firmnum = firmnum.drop("Unnamed: 0", axis = 1)

#!summary statistics 
#*all data
#how often do patents cite another patent?
cit = cites.groupby("src").count()
summary = pd.DataFrame(cit["dst"].describe()).T
"""
#how often is a patent cited?
cited = cites.groupby("dst").count() 
summary_2 = pd.DataFrame(cited["src"].describe()).T
"""
#*reduced datasets 
df_full = pd.read_csv("data/net_df.csv")
df_full = df_full.drop("Unnamed: 0", axis = 1)
#now create subsets of df_full which contian different number of citations 
#see prelim_analysis.pdf for more 
#dropping missing citation src or dst 
df_2 = df_full.dropna(how = "any")
#dropping self citations 
df_3 = df_2[df_2["owner_src"] != df_2["owner_dst"]]
#only keeping unique edges 
df_4 = df_3.drop_duplicates(["owner_src", "owner_dst"], keep = "first")

#how often do patents cite other patents?
sum_citations = pd.DataFrame()
for i, df in enumerate([df_full, df_2, df_3, df_4]): 
    row = str(i)
    group = df.groupby("src").count()
    sum_citations[row] = group["dst"].describe()
sum_citations = sum_citations.T 

"""
#how often is a patent cited? 
sum_cited = pd.DataFrame() 
for i, df in enumerate([df_full, df_2, df_3, df_4]): 
    row = str(i)
    group = df.groupby("dst").count()
    sum_cited[row] = group["src"].describe()
sum_cited = sum_cited.T 
"""