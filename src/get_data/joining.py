import pandas as pd 

"""
This file creates one dataset for grant_firm.csv, grant_grant.scv and grant_cite.csv 
for data downloaded and processed separately (namely from 1976 to 1989 is joined with data 
from 1990 to 2000)
"""
#set up working directory
#set up working directory 
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

#DATA
#read in necessary data
#df with firmnum and patnum up to 89 
df_grant89 = pd.read_csv("data/tables_to2000/grant_firm_to89.csv")
#df with firmunm and patnum up to 00
df_grant00 = pd.read_csv("data/tables_to2000/grant_firm_to00.csv")
#append together to get one dataset up to 2000
df_grant = df_grant89.append(df_grant00)

df_grant.to_csv("output/grant_firm.csv")

#df with grant information up to 89 
main89 = pd.read_csv("data/tables_to2000/grant_grant_to89.csv")
#same with data up to 2000
main00 = pd.read_csv("data/tables_to2000/grant_grant_to00.csv")
#append togeether to get one dataset up to 2000 
main = main89.append(main00)

main.to_csv("output/grant_grant.csv")

#get citations up to 89 
cites89 = pd.read_csv("data/tables_to2000/grant_cite_to89.csv")
#get citations up to 00
cites00 = pd.read_csv("data/tables_to2000/grant_cite_to00.csv")
#append to get a complete dataset up to 2000 
cites = cites89.append(cites00)

cites.to_csv("output/grant_cite.csv")