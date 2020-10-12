import pandas as pd 
import os 

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

df_firm_grant = pd.read_csv("data/tables2000to2020/grant_firm.csv") 
print("read grant")
grant_info = pd.read_csv("data/df_info.csv")
print("read grant_info")
df_cite = pd.read_csv("data/tables2000to2020/grant_cite.csv")
print("read citations")
df_cite = df_cite.dropna()

owner_source = df_cite.merge(df_firm_grant, how = "left", left_on = "src", right_on = "patnum")
owner_source = owner_source.rename(columns = {"firm_num": "firm_src"})
owner_source.head()
print("merge 1/4")
dst_source = owner_source.merge(df_firm_grant, how = "left", left_on = "dst", right_on = "patnum")
dst_source = dst_source.rename(columns = {"firm_num": "firm_dst"})
print("merge 2/4")

keep = "patnum"
b_src = grant_info
b_src.columns = b_src.columns.map(lambda x: x + "_src" if x != keep else x)
b_dst = grant_info 
b_dst.columns = b_dst.columns.map(lambda x: x + "_dst" if x != keep else x)

dst_source = dst_source.merge(b_src, how = "left", left_on = "src", right_on = "patnum")
print("merge 3/4")
dst_source = dst_source.merge(b_dst, how = "left", left_on = "dst", right_on = "patnum")
print("merge 4/4")
df12 = dst_source 
df12["firm_src"] = df12["firm_src"].astype(float)
df13 = df12
df13["firm_dst"] = df13["firm_dst"].astype(float)

df13["srcdst"] = [(x, y) for x, y in zip(df13["firm_src"], df13["firm_dst"])]

df2 = df13.dropna()
df3 = df2[df2["firm_src"] != df2["firm_dst"]]
df4 = df3.drop_duplicates(["srcdst"])

df2.to_csv("data/df2to2020.csv")
df3.to_csv("data/df3to2020.csv")
df4.to_csv("data/df4to2020.csv")

len(df3)
len(df2)