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

#! Missings inquiry 
#number of obs.: 269800
#ids matched to single firm_num
firm_to00 = pd.read_csv("data/tables_to2000/firm_to00.csv")
firm_to89 = pd.read_csv("data/tables_to2000/firm_to89.csv")
firm = firm_to89.append(firm_to00)

#firm_num matched to single id's
#number of obs.: 38646
match_to00 = pd.read_csv("data/tables_to2000/match_to00.csv")
match_to89 = pd.read_csv("data/tables_to2000/match_to89.csv")
match = match_to89.append(match_to00)
#!but apparently not the same 

#number of obs.: 223442
pair_to00 = pd.read_csv("data/tables_to2000/pair_to00.csv")
pair_to89 = pd.read_csv("data/tables_to2000/pair_to89.csv")
pair = pair_to89.append(pair_to00)

#number of obs.: 269800
name_to00 = pd.read_csv("data/tables_to2000/name_to00.csv")
name_to89 = pd.read_csv("data/tables_to2000/name_to89.csv")
name = name_to89.append(name_to00)

#number of obs.: 1986871
grant_match_to89 = pd.read_csv("data/tables_to2000/grant_match_to89.csv")
grant_match_to00 = pd.read_csv("data/tables_to2000/grant_match_to00.csv")
grant_match = grant_match_to89.append(grant_match_to00)

#number of obs.: 1986871
grant_firm_to89 = pd.read_csv("data/tables_to2000/grant_firm_to89.csv")
grant_firm_to00 = pd.read_csv("data/tables_to2000/grant_firm_to00.csv")
grant_firm = grant_firm_to89.append(grant_firm_to00)


firm_num_grant = grant_firm["firm_num"].tolist()
firm_num_grant = list(dict.fromkeys(firm_num_grant))
firm_num_firm = firm["firm_num"].tolist()
firm_num_firm = list(dict.fromkeys(firm_num_firm))
firm_num_grant == firm_num_firm #True ! len = 156150
#so firm numbers in firm data are same as in firm_num and patent_num matching 

grant_grant_to89 = pd.read_csv("data/tables_to2000/grant_grant_to89.csv")
grant_grant_to00 = pd.read_csv("data/tables_to2000/grant_grant_to00.csv")
grant_grant = grant_grant_to89.append(grant_grant_to00)
firm_list = grant_grant["owner"].tolist()
firm_list = list(dict.fromkeys(firm_list))
len(firm_list) #270048

grant_cite_to89 = pd.read_csv("data/tables_to2000/grant_cite_to89.csv")
grant_cite_to00 = pd.read_csv("data/tables_to2000/grant_cite_to00.csv")
grant_cite = grant_cite_to89.append(grant_cite_to00)

unique_src = list(dict.fromkeys(grant_cite["src"].tolist()))
len(unique_src) #=2375231
unique_dst = list(dict.fromkeys(grant_cite["dst"].tolist()))
len(unique_dst) #3651557

pats = grant_cite["src"].append(grant_cite["dst"])
pats = pats.drop_duplicates(keep = False)
len(pats) #4251496

#!are more dst or more src owners missing? 
#*src
#there are duplicates within the owner list which need to be dropped 
#otherwise merge (even with how = "left") adds rows/duplicates 
src = pd.DataFrame(grant_cite["src"].drop_duplicates())
owners = grant_grant[["patnum", "owner"]]
owners_nona = owners.dropna(how = "any") 
diff = len(owners) - len(owners_nona) #449354
owners_nodup = owners_nona.drop_duplicates("patnum", keep = "last")
diff = len(owners_nona) - len(owners_nodup) #5

src_owner = src.merge(owners_nodup, left_on = "src", right_on = "patnum", how = "left")
miss_count_src = src_owner["owner"].isnull().sum() #src missing owners: 442988 
have_count_src = (src_owner["owner"].isnull() == False).sum() #1932243

#*dst
dst = pd.DataFrame(grant_cite["dst"].drop_duplicates())

dst_owner = dst.merge(owners_nodup, left_on = "dst", right_on = "patnum", how = "left")
miss_count_dst = dst_owner["owner"].isnull().sum() #src missing owners: 2176689 
have_count_dst = (dst_owner["owner"].isnull() == False).sum() #1474868

#!check out how merging works out now 

merge_src = cites.merge(owners_nodup, left_on = "src", right_on = "patnum", how = "left")
merge_src = merge_src.drop("patnum", axis = 1)

merge_dst = merge_src.merge(owners_nodup, left_on = "dst", right_on = "patnum", how = "left")
merge_dst = merge_dst.drop("patnum", axis = 1)

df_full = merge_dst.rename(columns = {"owner_x": "owner_src", "owner_y": "owner_dst"})
df2 = df_full.dropna(how = "any")
df3 = df2[df2["owner_src"] != df2["owner_dst"]]
df4 = df3.drop_duplicates(["owner_src", "owner_dst"], keep = False)

for i, x in enumerate([df_full, df2, df3, df4]): 
    print(str(i) + ": " + str(len(x)))