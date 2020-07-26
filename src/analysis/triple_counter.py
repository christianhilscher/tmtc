import numpy as np
import pandas as pd
import networkx as net
import os

#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_ch)

#read in all data
#citations
cites = pd.read_csv(wd_ch + "data/grant_cite.csv")
#main file
main = pd.read_csv(wd_ch + "data/grant_grant.csv")
#ipc (what is this?)
ipc = pd.read_csv(wd_ch + "data/grant_ipc.csv")


#! Goal
#* filter mutual connections between two firms
#* check whether they are overlapping

#!Prepare data
#we don't need the patent number but its holder
#thus, merge cites with main - use a reduced form of the latter for better oversight (for now)
main_red = main[['patnum', 'owner']]
#merge reduced main with the citations to get owner names of src
merged = cites.merge(main_red, left_on = 'src', right_on = 'patnum', how = 'inner')
merged = merged.rename(columns = {'owner': 'owner_src'})
merged = merged.drop('patnum', axis = 1)
#merge the new df with main AGAIN, but this time based on dst to get firm
#names of dst owners
merged_2 = merged.merge(main_red, left_on = 'dst', right_on = 'patnum', how = 'inner')
merged_2 = merged_2.rename(columns = {'owner': 'owner_dst'})
#drop all rows which have no dst owners since they are of no use
matched = merged_2.dropna(how = 'any').drop('patnum', axis = 1)

#drop everything where owner_src == owner_dst

#!Network analysis
#create a network of df using NetworkX lib
network = net.convert_matrix.from_pandas_edgelist(matched, source = 'owner_src', target = 'owner_dst', create_using = net.DiGraph())
