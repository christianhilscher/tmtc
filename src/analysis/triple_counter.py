import numpy as np
import pandas as pd
import networkx as nx
import os

#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/src/"
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
    merged = left.merge(right, left_on = on[0], right_on = on[1])
    merged = merged.drop(drop, axis = 1)
    merged = merged.rename(columns = {rename[0]: rename[1]})
    return(merged)

def get_first(number, first = 4):
    first = int(str(number)[:first])
    return(first)

def mutuals(G):
    """
    A function to find the list of nodes that are successors as well as 
    predecessors of node n in a directed networkx graph G.
    This is done for all nodes and dictionary returned is structured as 
    {node: list of nodes that are predec and succec, node2: ...}
    G: directed Networkx graph
    """
    node_dict = {}
    for x in list(G.nodes):
        neigh = list(G.neighbors(x))
        predec = list(G.predecessors(x))
        both_dir = []
        for y in neigh: 
            if y in predec: 
                both_dir.append(y)
        node_dict[x] = both_dir
    return(node_dict)

#DATA
#read in all data
#citations
cites = pd.read_csv("get_data/data/tables/grant_cite.csv")
#main file 
main = pd.read_csv("get_data/data/tables/grant_grant.csv")
#ipc (what is this?)
ipc = pd.read_csv("get_data/data/tables/grant_ipc.csv")

#I don't think we need the ids if we trust the pairing
firmnum_grant = pd.read_csv("get_data/data/tables/grant_firm.csv")
firmnums = pd.read_csv("get_data/data/tables/match.csv")

matched = merger(cites, firmnum_grant, ('src', 'patnum'), ('firm_num', 'owner_src'), 'patnum')
matched_total = merger(matched, firmnum_grant, ('dst', 'patnum'), ('firm_num', 'owner_dst'), 'patnum')

year_src = main[['pubdate', 'patnum']]
year_src['pubdate'] = year_src['pubdate'].apply(get_first, args = [4])
matched_total = merger(matched_total, year_src, ('src', 'patnum'), ('pubdate', 'year'), 'patnum')

net_df = matched_total[['owner_src', 'owner_dst', 'year']]

#NETWORK
#initialize empty dictionaries to be filled with year: value
tri_dict = {}
citations_dict = {}
thicket_dict = {}
#initialize empty graph 
G = nx.DiGraph() 
#use the unique firm numbers as nodes of the graph
nodes = list(dict.fromkeys(firmnums['firm_num'].tolist()))
G.add_nodes_from(nodes)
#total citations counter
tot_ref = 0
#now loop over all years  
for year in range(1990, 2001):
    """
    this loop: 
        - gets data for respective year 
        - adds citations from this year as edges to G 
        - makes neighbor analysis
        - creates a new graph only with nodes that have mutually directed edges 
        - counts triangles and fills up initilaized dicts
    """
    matched_year = net_df[net_df['year'] == year]
    tot_ref = tot_ref + len(matched_year)
    #add nodes 
    edges = list(zip(matched_year['owner_src'], matched_year['owner_dst']))
    edges = list(set([i for i in edges]))
    G.add_edges_from(edges)
    node_dict = mutuals(G)
    #delete nodes that have no nodes connected as mutual successors as predecessors
    for k, v in list(node_dict.items()): 
        if v == []: 
            del node_dict[k]

    G_new = nx.Graph(node_dict)
    tris = list(nx.triangles(G_new).values())
    tris_arr = np.array(tris)
    tris_sum = np.sum(tris_arr)/3
    thicket_dict[str(year)] = tris_sum/tot_ref
    tri_dict[str(year)] = tris_sum 
    citations_dict[str(year)] = tot_ref

#plot 
from bokeh.plotting import figure, output_notebook, show 
output_notebook()
p = figure(plot_width = 500, plot_height = 500, 
        x_axis_label = 'Year', y_axis_label = 'share of patent thickets', 
            )
p.line(list(thicket_dict.keys()), list(thicket_dict.values()), 
        line_width = 2)
show(p)