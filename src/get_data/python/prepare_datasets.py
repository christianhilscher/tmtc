import pandas as pd 
import os 

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

#! Adding IPC classification
def add_ipc(df, df_ipc): 
    df_ipc = df_ipc.drop_duplicates(["ipc_code"])
    df = df.dropna(subset = ["ipc"])
    df["ipc_code"] = df["ipc"].astype(str).str[:4]
    df_ipc = df.merge(df_ipc, on = "ipc_code")    
    return(df_ipc)

#! Adding NBER classification
def add_nber(df, df_nber, df_nber_cat, df_nber_subcat): 
    #merging the title categories
    df_cats = df_nber[["patent_id", "category_id", 
                    "subcategory_id"]].merge(df_nber_cat, left_on = "category_id", right_on = "id")
    df_cats = df_cats.rename(columns = {"title": "category_title"})
    df_cats = df_cats.merge(df_nber_subcat, left_on = "subcategory_id", right_on = "id")
    df_cats = df_cats.rename(columns = {"title": "subcategory_title"})
    df_cats = df_cats.drop(["id_x", "id_y"], axis = 1)
    df = df.merge(df_cats, left_on = "patnum", right_on = "patent_id")  
    return(df)

def makeyear(df, yearcol): 
    df[yearcol] = df[yearcol].astype(str).str[:4]
    df[yearcol] = df[yearcol].astype(float)
    return(df)

def add_info(df, df_ipc, df_nber, df_nber_cat, df_nber_subcat, yearcol): 
    """
    Add all of the three functions above
    """
    df = makeyear(df, yearcol)
    a = add_ipc(df, df_ipc) 
    b = add_nber(a, df_nber, df_nber_cat, df_nber_subcat)
    return(b)

df_firm_grant = pd.read_csv("data/tables2000to2020/grant_firm.csv") 
print("read firm_grant")
df_grants = pd.read_csv("data/tables2000to2020/grant_grant.csv")
print("read grant_grant")
df_cite = pd.read_csv("data/tables2000to2020/grant_cite.csv")
df_cite = df_cite.dropna()
print("read citations")

df_ipc = pd.read_csv("data/ipcs.csv")
print("read ipcs")
df_nber = pd.read_csv("data/nber.tsv", sep = "\t")
df_nber_cat = pd.read_csv("data/nber_category.tsv", sep = "\t")
df_nber_subcat = pd.read_csv("data/nber_subcategory.tsv", sep = "\t")
print("read nber")

grant_info = add_info(df_grants, df_ipc, df_nber, df_nber_cat, df_nber_subcat, "pubdate")

owner_source = df_cite.merge(df_firm_grant, how = "left", left_on = "src", right_on = "patnum")
owner_source = owner_source.rename(columns = {"firm_num": "firm_src"})
print("merge 1/4")
dst_source = owner_source.merge(df_firm_grant, how = "left", left_on = "dst", right_on = "patnum")
dst_source = dst_source.rename(columns = {"firm_num": "firm_dst"})
print("merge 2/4")

b_src = grant_info 
b_dst = grant_info 
dst_source = dst_source.merge(b_src, how = "left", left_on = "src", right_on = "patnum")
print("merge 3/4")
dst_source = dst_source.merge(b_dst, how = "left", left_on = "dst", right_on = "patnum")
print("merge 4/4")

oldcols_src = [col for col in dst_source.columns if col.endswith("_x")]
colnames_src = [col + "_src" for col in dst_source.columns if col.endswith("_x")]
oldcols_dst = [col for col in dst_source.columns if col.endswith("_y")]
colnames_dst = [col + "_dst" for col in dst_source.columns if col.endswith("_y")]

dst_source = dst_source.rename(columns = {i: j for i, j in zip(oldcols_src, colnames_src)})
dst_source = dst_source.rename(columns = {i: j for i, j in zip(oldcols_dst, colnames_dst)})

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