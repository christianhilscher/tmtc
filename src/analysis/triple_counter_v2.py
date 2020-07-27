import numpy as np
import pandas as pd
import networkx as nx
import os

#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_lc)

#functions 
def get_first(number, first = 4): 
    """
    Get first 'first' digits of supplied 'number'.
    """
    return(int(str(number)[:4]))

#read in all data
#citations
cites = pd.read_csv("src/get_data/data/tables/grant_cite.csv")
#main file 
main = pd.read_csv("src/get_data/data/tables/grant_grant.csv")
#ipc (what is this?)
ipc = pd.read_csv("src/get_data/data/tables/grant_ipc.csv")

#! Goal 
#* filter mutual connections between two firms 
#* check whether they are overlapping 

#!Prepare data 
#we don't need the patent number but its holder 
#thus, merge cites with main - use a reduced form of the latter for better oversight (for now)
main_red = main[['patnum', 'owner', 'pubdate']]
#merge reduced main with the citations to get owner names of src 
merged = cites.merge(main_red, left_on = 'src', right_on = 'patnum', how = 'inner')
merged = merged.rename(columns = {'owner': 'owner_src'})
merged = merged.drop(['patnum', 'pubdate'], axis = 1)
#merge the new df with main AGAIN, but this time based on dst to get firm 
#names of dst owners
merged_2 = merged.merge(main_red, left_on = 'dst', right_on = 'patnum', how = 'inner')
matched = merged_2.rename(columns = {'owner': 'owner_dst'})
#turn publication date into year only 
matched['pubdate'] = matched['pubdate'].apply(get_first, args = [4])

#!Network Analysis
thicket_dict = {}
citations_dict = {}
triangle_dict = {}
for year in range(1990, 2001):
    year = 1992
    matched_year = matched[matched['pubdate'] <= year]
    tot_ref = len(matched_year)
    #only keep src that is also in dst, otherwise not possible to have mutually directed edges
    matched_year = matched_year[matched_year['owner_dst'].isin(matched_year['owner_src'])].reset_index(drop = True)
    #drop where dst is not known, aka all rows that have owner_dst as nan
    matched_year = matched_year.dropna(how = 'any').drop('patnum', axis = 1)
    #create graph 
    G = nx.DiGraph()
    #add nodes 
    owners_src = matched_year['owner_src'].tolist()
    owners_dst = matched_year['owner_dst'].tolist()
    nodes = owners_src + owners_dst
    #remove duplicates of firms
    nodes = list(dict.fromkeys(nodes))
    G.add_nodes_from(nodes)
    #add edges
    edges = list(zip(matched_year['owner_src'], matched_year['owner_dst']))
    edges = list(set([i for i in edges]))
    G.add_edges_from(edges)
    nodes_dict = {}
    adj_mat = nx.adjacency_matrix(G)
    adj_mat_dense = adj_mat.todense()
    node_dict = {}
    for x in list(G.nodes):
        neigh = list(G.neighbors(x))
        predec = list(G.predecessors(x))
        both_dir = []
        for y in neigh: 
            if y in predec: 
                both_dir.append(y)
        node_dict[x] = both_dir

    for k, v in list(node_dict.items()): 
        if v == []: 
            del node_dict[k]
    
    G_new = nx.Graph(node_dict)
    tris = list(nx.triangles(G_new).values())
    tris_arr = np.array(tris)
    tris_sum = np.sum(tris_arr)/3
    triangle_dict[str(year)] = tris_sum 
    citations_dict[str(year)] = tot_ref
    thicket_dict[str(year)] = tris_sum/tot_ref