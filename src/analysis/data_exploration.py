import numpy as np 
import pandas as pd 
import os 

#set up working directory 
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)


#!#####################
#! Missings inquiry 
#!#####################

#*########
#! Data 
#*########
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

#number of obs.: 2436225
grant_grant_to89 = pd.read_csv("data/tables_to2000/grant_grant_to89.csv")
grant_grant_to00 = pd.read_csv("data/tables_to2000/grant_grant_to00.csv")
grant_grant = grant_grant_to89.append(grant_grant_to00)

#number of obs.: 19581061
grant_cite_to89 = pd.read_csv("data/tables_to2000/grant_cite_to89.csv")
grant_cite_to00 = pd.read_csv("data/tables_to2000/grant_cite_to00.csv")
grant_cite = grant_cite_to89.append(grant_cite_to00)


#*########
#! Number of patents
#*########

#*how many unique patents exist? 
#main file -> grant_grant
pats = grant_grant["patnum"].drop_duplicates(keep = "first")
no_pats = len(pats) #2436218

#citations
#how many unique patents in src?  
pats_cite = grant_cite["src"].drop_duplicates(keep = "first")
no_pats_cite = len(pats_cite) #2,375,231
#how many unique patents in dst?
pats_cited = grant_cite["dst"].drop_duplicates(keep = "first")
no_pats_cited = len(pats_cited) #3,651,557
#how many unique patents in src and dst combined? 
pats_cit = pats_cite.append(pats_cited).drop_duplicates(keep = "first")
no_pats_cit = len(pats_cit) #4,251,496

#firm_num - patnum allocation 
pats_firmnum = grant_firm["patnum"].drop_duplicates(keep = "first")
no_pats_firmnum = len(pats_firmnum) #1,986,866

"""
Summary:
    - cannot (!) have information on all patents that are contained 
    in citation info df; we have info on ~2.4 million patents, while 
    citations in total contain ~4.2 million patents overall (unique) 

    - a firm_num is only matched to ~1.9 million patents, 
    hence additionally ~500k patents are missing when matching firm_num 
    to patent -> why? WHAT IS FIRM_NUM EXACTLY? 
    
    -next up: what is the larger source of discrepancy between citation 
    patents and info patents? src or dst?  
"""

#*########
#! Missings per category (src and dst)
#*########

#*get an owner list 
owner = grant_grant[["patnum", "owner"]]
owner = owner.drop_duplicates(keep = "first") #5 duplicates exist

#*info missing on src 
#check how many of the UNIQUE src patents have no matched owner
src = pd.DataFrame(grant_cite["src"].drop_duplicates())
src_owner = src.merge(owner, left_on = "src", right_on = "patnum", how = "outer")
"""
-> use outer join such that I keep 
    - pats that are not src but in main 
    - pats that are in src but not in main 
Now, look for 
    1. src - patnum matched, owner NaN (src_1)
    2. src NaN, patnum exists (src_2)
    3. src exists, patnum NaN (src_3)
"""
src_1 = src_owner[src_owner["src"] == src_owner["patnum"]] 
#how many matched pats do not have an owner?
src_1_miss = src_1["owner"].isnull().sum() #442,990 

src_2 = src_owner[(src_owner["src"].isnull()) & (src_owner["patnum"].isnull() == False)]
#how many pats are mentioned in main but not in src?
src_2_miss = len(src_2) #60,987

src_3 = src_owner[(src_owner["src"].isnull() == False) & (src_owner["patnum"].isnull())]
#how many pats are mentioned in src but not in main? 
src_3_miss = len(src_3) #0 !


#*info missing on dst 
dst = pd.DataFrame(grant_cite["dst"].drop_duplicates())
dst_owner = dst.merge(owner, left_on = "dst", right_on = "patnum", how = "outer")
"""
-> use outer join such that I keep 
    - pats that are not dst but in main 
    - pats that are in dst but not in main 
Now, look for 
    1. dst - patnum matched, owner NaN (dst_1)
    2. dst NaN, patnum exists (dst_2)
    3. dst exists, patnum NaN (dst_3)
"""
dst_1 = dst_owner[dst_owner["dst"] == dst_owner["patnum"]] 
#how many matched pats do not have an owner?
dst_1_miss = dst_1["owner"].isnull().sum() #333,617

dst_2 = dst_owner[(dst_owner["dst"].isnull()) & (dst_owner["patnum"].isnull() == False)]
#how many pats are mentioned in main but not in dst?
dst_2_miss = len(dst_2) #627,735

dst_3 = dst_owner[(dst_owner["dst"].isnull() == False) & (dst_owner["patnum"].isnull())]
#how many pats are mentioned in dst but not in main? 
dst_3_miss = len(dst_3) # 1,843,072!

#*########
#! Shares of missings
#*########

"""
- have number of missings in each relevant combination now 
for src and dst alone, what about combined? 
"""

src_dst = pd.DataFrame(src["src"].append(dst["dst"]).drop_duplicates()).rename(columns = {0: "pat"})
src_dst["dst"] = src_dst["pat"].isin(dst["dst"])
src_dst["src"] = src_dst["pat"].isin(src["src"])

src_dst_owner = src_dst.merge(owner, left_on = "pat", right_on = "patnum", how = "left", indicator = True)
tot = src_dst_owner
"""
Now want to find out: 
    1. how many "pat" have no match? 
    2. how many "pat" and src == True & dst == False have no match? What is share? 
    3. how many "pat" and dst == True & src == False have no match? What is share? 
    4. how many "pat" and dst == True & src == True have no match? What is share? 
    5. how many owners of "pat" that are matched are missing? 
    6. how many owners of "pat" and src == True & dst == False that are matched are missing? What is share? 
    7. how many owners of "pat" and dst == True & src == False that are matched are missing? What is share? 
    8. how many "pat" and dst == True & src == True have no match? What is share? 
"""

#*1. 
pat_1 = tot[tot["_merge"] == "left_only"]
#*A: 1,843,073

#*2. 
pat_2 = pat_1[(pat_1["src"] == True) & (pat_1["dst"] == False)]
#*A: 0; 0% 

#*3. 
pat_3 = pat_1[(pat_1["dst"] == True) & (pat_1["src"] == False)]
#*A: 1,843,073; 100%

#*4. 
pat_4 = pat_1[(pat_1["dst"] == True) & (pat_1["src"] == True)]
#*A: there is noverlap in these

#*5. 
both = tot[tot["_merge"] == "both"]
pat_5 = both["owner"].isnull().sum()
#*A: 446,103

#*6.
both_src = both[(both["src"] == True) & (both["dst"] == False)]
pat_6 = both_src["owner"].isnull().sum()
share_6 = pat_6/pat_5
#*A: 112,486; 25.22%

#*7.
both_dst = both[(both["src"] == False) & (both["dst"] == True)]
pat_7 = both_dst["owner"].isnull().sum()
share_7 = pat_7/pat_5
#*A: 3113; 0.698%

#*8. 
both_srcdst = both[(both["src"] == True) & (both["dst"] == True)]
pat_8 = both_srcdst["owner"].isnull().sum()
share_8 = pat_8/pat_5
#*A: 330504; 74.01%

"""
Summary: 
    - not matched patents are ONLY contained in dst, not in src 
    - i.e. missing info on dst, not on src 
    - missing owners are mostly of patents which are both, src and dst
        - this is quite bad for us since we are interested in patents that are both/firms that own both
"""