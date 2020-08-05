import numpy as np 
import pandas as pd 
import os 

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_lc)

#FUNCTIONS 
def merger(left, right, on, rename, drop):
    """
    inner merge left with right
    left: left df 
    right: right df 
    on: tuple, (left_on, right_on)
    rename: tuple, (old_name, new_name)
    drop: string of column name to drop 
    """
    merged = left.merge(right, left_on = on[0], right_on = on[1], how = 'outer')
    merged = merged.drop(drop, axis = 1)
    merged = merged.rename(columns = {rename[0]: rename[1]})
    return(merged)

def get_first(number, first = 4):
    first = int(str(number)[:first])
    return(first)

#DATA
#read in all data
#df with firmnum and patnum up to 89 
df_grant89 = pd.read_csv("data/tables_to2000/grant_firm_to89.csv")
#df with firmunm and patnum up to 00
df_grant00 = pd.read_csv("data/tables_to2000/grant_firm_to00.csv")
#append together to get one dataset up to 2000
df_grant = df_grant89.append(df_grant00)

#df with grant information up to 89 
main89 = pd.read_csv("data/tables_to2000/grant_grant_to89.csv")
#same with data up to 2000
main00 = pd.read_csv("data/tables_to2000/grant_grant_to00.csv")
#append togeether to get one dataset up to 2000 
main = main89.append(main00)

#get citations up to 89 
cites89 = pd.read_csv("data/tables_to2000/grant_cite_to89.csv")
#get citations up to 00
cites00 = pd.read_csv("data/tables_to2000/grant_cite_to00.csv")
#append to get a complete dataset up to 2000 
cites = cites89.append(cites00)

matched = merger(cites, df_grant, ('src', 'patnum'), ('firm_num', 'owner_src'), 'patnum')
matched_total = merger(matched, df_grant, ('dst', 'patnum'), ('firm_num', 'owner_dst'), 'patnum')

year_src = main[['pubdate', 'patnum']]
year_src = year_src.dropna(how = "any")
year_src['pubdate'] = year_src['pubdate'].apply(get_first, args = [4])
matched_total = merger(matched_total, year_src, ('src', 'patnum'), ('pubdate', 'year'), 'patnum')

net_df = matched_total[['owner_src', 'owner_dst', 'year']]
#write to csv
net_df.to_csv("data/net_df.csv")