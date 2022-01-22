import pandas as pd 
import numpy as np 

#set up working directory 
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

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



owners_info = main[["patnum", "pubdate", "appdate", "ipc", "ipcver", "owner"]]
owners_info = owners_info.drop_duplicates("patnum")

merged_src = cites.merge(owners_info, left_on = "src", right_on = "patnum", how = "outer", indicator = True)
merged_src = merged_src[["src", "dst", "pubdate", "ipc", "ipcver", "owner", "_merge"]]
merged_src = merged_src.rename(columns = {"pubdate": "pub_src", "ipc": "ipc_src", "ipcver": "ipcver_src", 
                                            "owner": "owner_src", "_merge": "merge_src"})
merged = merged_src.merge(owners_info, left_on = "dst", right_on = "patnum", how = "outer", indicator = True)
merged_reduc = merged[merged["_merge"] == "both"]
merged_reduc = merged_reduc[merged["merge_src"] == "both"] 

#*########
#! Summary grant_cite (all citations)
#*########
summary_df = pd.DataFrame()

grouped_src = cites.groupby("src").count()
summary_src = pd.DataFrame(grouped_src["dst"].describe()).T
grouped_dst = cites.groupby("dst").count()
summary_dst = pd.DataFrame(grouped_dst["src"].describe()).T
summary_df = summary_df.append(summary_dst)
summary_df = summary_df.append(summary_src)
summary_df = summary_df.rename(index = {"src": "Cited (total)", "dst": "Citing (total)"})

#*########
#! Summary grant_cite (all citations we have info on)
#*########

grouped_src = merged_reduc[["src", "dst"]].groupby("src").count()
summary_src = pd.DataFrame(grouped_src["dst"].describe()).T
grouped_dst = merged_reduc[["src", "dst"]].groupby("dst").count()
summary_dst = pd.DataFrame(grouped_dst["src"].describe()).T
summary_df = summary_df.append(summary_dst)
summary_df = summary_df.append(summary_src)
summary_df = summary_df.rename(index = {"src": "Cited (reduced)", "dst": "Citing (reduced)"})