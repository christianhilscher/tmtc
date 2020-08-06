import numpy as np
import pandas as pd
import networkx as nx
import os

#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_lc)

#FUNCTIONS
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
#read in net_df csv created in "create_netdf.py" 
net_df = pd.read_csv('data/net_df.csv')
net_df = net_df.drop('Unnamed: 0', axis = 1)
#net_df contains ALL citations, i.e. it is df_full (see description of process)
df_full = net_df
#df_full is df_1 

#now create subsets of df_full which contian different number of citations 
#see prelim_analysis.pdf for more 
#dropping missing citation src or dst 
df_2 = df_full.dropna(how = "any")
#dropping self citations 
df_3 = df_2[df_2["owner_src"] != df_2["owner_dst"]]
#only keeping unique edges 
#to drop all duplicates but the initial entry I guess I have to set keep = False (see pandas docs)
df_4 = df_3.drop_duplicates(["owner_src", "owner_dst"], keep = False)
#NETWORK

#FOR NOW: using df_3 for edges 
#initialize empty dictionaries to be filled with year: value
tri_dict = {}
citations_dict = {}
thicket_dict = {}
#initialize empty graph 
G = nx.DiGraph() 

#create nodes from combined list of owners_src and owners_dst 
#drop duplicates of combined list such that each firm only appears once
owners_src = df_2["owner_src"].tolist()
owners_dst = df_2["owner_dst"].tolist()
total = owners_src + owners_dst
total = list(map(int, total))
tot_uniq = list(dict.fromkeys(total))

#add nodes to graph 
nodes = tot_uniq
G.add_nodes_from(nodes)
#total citations counter
tot_ref = 0
#now loop over all years  
for year in range(1976, 2001):
    """
    this loop: 
        - gets data for respective year 
        - adds citations from this year as edges to G 
        - makes neighbor analysis
        - creates a new graph only with nodes that have mutually directed edges 
        - counts triangles and fills up initialized dicts
    """
    matched_year = df_4[df_4['year'] == year]
    citations = len(df_full[df_full["year"] == year])
    tot_ref = tot_ref + citations
    matched_year = matched_year[matched_year['owner_src'] != matched_year['owner_dst']]
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
    print(str(year) + ' done')

#plot 
from bokeh.plotting import figure, output_notebook, show 
from bokeh.io import export_png
output_notebook()
p = figure(plot_width = 500, plot_height = 500, 
        x_axis_label = 'Year', y_axis_label = 'share of patent thickets', 
            )
p.line(list(thicket_dict.keys()), list(thicket_dict.values()), 
        line_width = 2)
show(p)
#export_png(p, "ouput/figure1.png")