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
df_2 = pd.read_csv("data/df2.csv")
df_3 = pd.read_csv("data/df3.csv")
df_4 = pd.read_csv("data/df4.csv")
df_disc = df_4[df_4["technology"] == "discrete"]
df_com = df_4[df_4["technology"] == "complex"]

#NETWORK
#initialize empty dictionaries to be filled "name: dict" for each different dataframe
tri_dict_all = {}
cit_dict_all = {}
thicket_dict_all = {}
#create nodes from combined list of owners_src and owners_dst 
#drop duplicates of combined list such that each firm only appears once
owners_src = df_4["firm_src"].tolist()
owners_dst = df_4["firm_dst"].tolist()
total = owners_src + owners_dst
total = list(map(int, total))
tot_uniq = list(dict.fromkeys(total))
#add nodes to graph 
nodes = tot_uniq
G = nx.DiGraph()
G.add_nodes_from(nodes)
#total citations counter
names = ["total", "discrete", "complex"]
dfs = [df_4, df_disc, df_com]
years = np.arange(1976, 2001)
#loop over names and dataframes
for name, df in zip(names, dfs): 
    #counter for total references
    tot_ref = 0
    #initialize empty dictionaries to be filled with year: value
    tri_dict = {}
    citations_dict = {}
    thicket_dict = {}
    #clean graph from all edges 
    G.remove_edges_from(list(G.edges()))
    print("edges removed")
    #now loop over all years
    for year in years:
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
    tri_dict_all[name] = tri_dict
    cit_dict_all[name] = citations_dict 
    thicket_dict_all[name] = thicket_dict
    print(name + "done") 

#thickets
thickets_total = thicket_dict_all["total"]
thickets_disc = thicket_dict_all["discrete"]
thickets_com = thicket_dict_all["complex"]
#triangles
tri_total = tri_dict_all["total"]
tri_disc = tri_dict_all["discrete"]
tri_com = tri_dict_all["complex"]
#citations
cit_total = cit_dict_all["total"]
cit_list = np.array(list(cit_total.values()))

#! Analysis by ipc 
ipcs = {}
for x, y, z in zip(df_2["firm_dst"], df_2["firm_src"], df_2["field_num"]):
    ipcs[(x, y)] = z
ipcs = 

#!Plot 
from bokeh.plotting import figure, output_notebook, show 
from bokeh.io import export_png
from bokeh.models import NumeralTickFormatter

output_notebook()

#*figure on absolute number of triples
p_abstrip = figure(plot_width = 500, plot_height = 500, 
        x_axis_label = 'Year', y_axis_label = "Absolute number of triples", 
        title = "Total number of triples")
p_abstrip.line(years, list(tri_total.values()), color = "blue", legend_label = "total")
p_abstrip.line(years, list(tri_disc.values()), color = "red", legend_label = "discrete")
p_abstrip.line(years, list(tri_com.values()), color = "orange", legend_label = "complex")
p_abstrip.legend.location = "top_left"
#p.yaxis.formatter = NumeralTickFormatter(format = "0000")
show(p_abstrip)
#export_png(p_abstrip, filename = "output/abs_triples_tech.png")

#*figure on share of triples relative to total citations
p_share = figure(plot_width = 500, plot_height = 500, 
        x_axis_label = 'Year', y_axis_label = "Percentage", 
        title = "Share of triples relative to all citations")
total_share = np.array(list(tri_total.values()))/cit_list
disc_share = np.array(list(tri_disc.values()))/cit_list
com_share = np.array(list(tri_com.values()))/cit_list
p_share.line(years, total_share, color = "blue", legend_label = "total")
p_share.line(years, disc_share, color = "red", legend_label = "discrete")
p_share.line(years, com_share, color = "orange", legend_label = "complex")
p_share.legend.location = "top_left"
show(p_share)
#export_png(p_share, filename = "output/shares_triples_totalcit")




df_full_count = df_full.groupby("field_num").count().reset_index()
df2_count = df_2.groupby("field_num").count().reset_index()
df4_count = df.groupby("field_num").count().reset_index()

ticks = [(x, y) for x, y in zip(df_2["field_num"], df_2["field"])]
ticks = list(dict.fromkeys(ticks))
ticks = dict(ticks)

y = df_full_count["field_num"].tolist()
right = df_full_count["ipc"].tolist()
p_full = figure(plot_width = 500, plot_height = 500, 
                x_axis_label = "count", title = "df full")
p_full.hbar(y = y, right = right, height = 0.9)
p_full.yaxis.ticker = list(ticks.keys())
p_full.yaxis.major_label_overrides = ticks
p.xaxis.formatter = NumeralTickFormatter(format = "0000")
show(p_full)
export_png(p_full, filename ="p_full.png")

y = df4_count["field_num"].tolist()
right = df4_count["ipc"].tolist()
p_4 = figure(plot_width = 500, plot_height = 500, 
                x_axis_label = "count", title = "df 4")
p_4.hbar(y = y, right = right, height = 0.9)
p_4.yaxis.ticker = list(ticks.keys())
p_4.yaxis.major_label_overrides = ticks
p.xaxis.formatter = NumeralTickFormatter(format = "0000")
show(p_4)
export_png(p_4, filename = "p_4.png")


y = df2_count["field_num"].tolist()
right = df2_count["ipc"].tolist()
p_2 = figure(plot_width = 500, plot_height = 500, 
                x_axis_label = "count", title = "df 2")
p_2.hbar(y = y, right = right, height = 0.9)
p_2.yaxis.ticker = list(ticks.keys())
p_2.yaxis.major_label_overrides = ticks
p.xaxis.formatter = NumeralTickFormatter(format = "0000")
show(p_2)
export_png(p_2, filename = "p_2.png")


#!figure df2 categories 
x = df4_count["field_num"].tolist()
top = df4_count["ipc"].tolist()
p = figure(plot_width = 600, plot_height = 600, toolbar_location = None)
p.vbar(x = x, top = top, width = 0.9)
p.xaxis.ticker = list(ticks.keys())
p.xaxis.major_label_overrides = ticks
p.xaxis.major_label_orientation = 0.8
show(p)
export_png(p, filename = "Field_Counts_vert.png")
