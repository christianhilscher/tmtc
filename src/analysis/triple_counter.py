import numpy as np
import pandas as pd
import networkx as nx
import os
from collections import Counter 
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
    G: directed Networkx Draph
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
df_full = pd.read_csv("data/df1.csv")
#now create subsets of df_full which contian different number of citations 
#see prelim_analysis.pdf for more 
#dropping missing citation src or dst 
df_2 = df_full.dropna(how = "any", subset = ["firm_dst", "firm_src"])
#dropping self citations 
df_3 = df_2[df_2["firm_src"] != df_2["firm_dst"]]
#only keeping unique edges 
#to drop all duplicates but the initial entry I guess I have to set keep = False (see pandas docs)
df_4 = df_3.drop_duplicates(["firm_src", "firm_dst"], keep = "first")

#NETWORK

#initialize empty dictionaries to be filled with year: value
tri_list = []
cit_list = []
thicket_list = []
#initialize empty graph 
G = nx.DiGraph() 

#create nodes from combined list of owners_src and owners_dst 
#drop duplicates of combined list such that each firm only appears once
df_discrete = df_2[df_2["technology"] == "discrete"]
owners_src = df_discrete["firm_src"].tolist()
owners_dst = df_discrete["firm_dst"].tolist()
total = owners_src + owners_dst
total = list(map(int, total))
tot_uniq = list(dict.fromkeys(total))

#add nodes to graph 
nodes = tot_uniq
G.add_nodes_from(nodes)
#total citations counter
tot_ref = 0
#loop over the different df as basis 
for df in [df_full, df_2, df_3, df_4]:
    df = df_3[df_3["technology"] == "discrete"]
    #initialize empty dictionaries to be filled with year: value
    tri_dict = {}
    citations_dict = {}
    thicket_dict = {}
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
        matched_year = df[df['year'] == year]
        citations = len(df_2[df_2["year"] == year])
        tot_ref = tot_ref + citations
        matched_year = matched_year[matched_year['firm_src'] != matched_year['firm_dst']]
        #add nodes 
        edges = list(zip(matched_year['firm_src'], matched_year['firm_dst']))
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
    tri_list.append(tri_dict)
    thicket_list.append(thicket_dict)
    cit_list.append(citations_dict)
    print('df done')


com = tri_list[0]
disc = tri_list[1]
#summed citations
totref_com = cit_list[0]
totref_sum = np.array(list(totref_com.values()))
#total triples 
tri_sum = np.sum(list(com.values())) + np.sum(list(disc.values()))
#ratios
com_ratios = np.array(list(com.values()))/totref_sum
disc_ratios = np.array(list(disc.values()))/totref_sum
#values 
com_val = np.array(list(com.values()))
com_val = ['{:f}'.format(x) for x in com_val]
com_val = [x.split(".")[0] for x in com_val]
disc_val = np.array(list(disc.values()))
disc_val = ['{:f}'.format(x) for x in disc_val]
disc_val = [x.split(".")[0] for x in disc_val]

com_trishare = np.array(list(com.values()))/tri_sum 
disc_trishare = np.array(list(disc.values()))/tri_sum

#plot 
from bokeh.plotting import figure, output_notebook, show 
from bokeh.io import export_png
from bokeh.models import NumeralTickFormatter
output_notebook()
p = figure(plot_width = 500, plot_height = 500, 
        x_axis_label = 'Year', y_axis_label = "Share of triples to total triples", 
            )
p.line(list(com.keys()), com_trishare, color = "blue", legend_label = "complex")
p.line(list(disc.keys()), disc_trishare, color = "red", legend_label = "discrete")
p.legend.location = "top_left"
p.yaxis.formatter = NumeralTickFormatter(format = "0.000")
show(p)
export_png(p, filename = "com_disc_triratio.png")