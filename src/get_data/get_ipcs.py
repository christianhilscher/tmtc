import pandas as pd 
import os 

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

df_ipc = pd.read_excel("data/ipc_technology.xls")
df_ipc = df_ipc.iloc[6:, [0, 1, 4, 7]]
df_ipc = df_ipc.rename(columns = {"IPC8 -Technology Concordance": "field_num", 
                                "Unnamed: 4": "field", 
                                "Unnamed: 1": "sector", "Unnamed: 7": "ipc_code"}).reset_index(drop = True)

df_ipc["field_num"] = df_ipc["field_num"].astype(str).str[:4]
df_ipc["technology"] = "complex"

for i in range(14, 24): 
    field = df_ipc["field_num"] == i
    df_ipc["technology"][field] = "discrete"

df_ipc.to_csv("data/ipcs.csv")