import numpy as np
import pandas as pd
import networkx as nx
import os
from collections import Counter 
#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_lc)

np.set_printoptions(suppress=True)

#**************
#! FUNCTIONS
#**************
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

def get_tri(df, years):
    #counter for total references
    tot_ref = 0
    #initialize empty dictionaries to be filled with year: value
    tri_dict = {}
    cit_dict = {}
    thicket_dict = {}
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
        #matched_year = matched_year[matched_year['firm_src'] != matched_year['firm_dst']]
        citations = len(df_2[df_2["year"] == year])
        tot_ref = tot_ref + citations
        #add edges
        edges = list(zip(matched_year['firm_src'], matched_year['firm_dst']))
        edges = list(set([i for i in edges]))
        G.add_edges_from(edges)
        G.number_of_edges()
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
        cit_dict[str(year)] = tot_ref
    return(thicket_dict, tri_dict, cit_dict)

def tech_plot(x, total, disc, com, title, ylab, xlab = "Year"):
    """
    Function to create plots with total, discrete and complex data. 
    """
    plot = figure(plot_wifth = 500, plot_height = 500, x_axis_label = xlab, 
                y_axis_label = ylab, title = title)
    plot.line(x, total, color = "blue", legend_label = "total")
    plot.line(x, disc, color = "red", legend_label = "discrete")
    plot.line(x, com, color = "orange", legend_label = "complex")
    plot.legend.location = "top_left"
    return(plot)

#**************
#! DATA
#**************
df_full = pd.read_csv("data/df1.csv")
df_2 = pd.read_csv("data/df2.csv")
df_3 = pd.read_csv("data/df3.csv")
df_4 = pd.read_csv("data/df4.csv")
df_disc = df_4[df_4["technology"] == "discrete"]
df_com = df_4[df_4["technology"] == "complex"]

#**************
#! NETWORK
#**************

#! Set up graph
#initialize empty dictionaries to be filled "name: dict" for each different dataframe
tri_dict_all = {}
cit_dict_all = {}
thicket_dict_all = {}
#create nodes from combined list of owners_src and owners_dst 
#drop duplicates of combined list such that each firm only appears once
owners_src = df_3["firm_src"].tolist()
owners_dst = df_3["firm_dst"].tolist()
total = owners_src + owners_dst
total = list(map(int, total))
tot_uniq = list(dict.fromkeys(total))
#set up graph
G = nx.DiGraph()
#add nodes to graph 
nodes = tot_uniq
G.add_nodes_from(nodes)

#! Total, discrete and complex technology triangles
#set up names for dictionaries
names = ["total", "discrete", "complex"]
#df to loop over
dfs = [df_4, df_disc, df_com]
#years of interest
years = np.arange(1976, 2001)

#loop over names and dataframes
for name, df in zip(names, dfs): 
    #clean graph from all edges 
    G.remove_edges_from(list(G.edges()))
    thicket_dict_all[name], tri_dict_all[name], cit_dict_all[name] = get_tri(df, years)
    print(name + " done")

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

#! Triangles by ipc
thickets_ipc = {} 
tri_ipc = {}
cit_ipc = {}
#remove all edges from G again 
G.remove_edges_from(list(G.edges()))
#get field and field_num pair
fields = [(x, y) for x,y in zip(df_3["field_num"], df_3["field"])]

fields = list(dict.fromkeys(fields))
field_nums = [x[0] for x in fields]
field_names = [x[1] for x in fields]
fields_df = pd.DataFrame({"field": field_names, "field_num": field_nums})
fields_df = fields_df.sort_values(by = "field_num", axis = 0).reset_index().drop("index", axis = 1)

for field in fields:
    G.remove_edges_from(list(G.edges()))
    df = df_3[df_3["field_num"] == 13]
    name = "Medical technology"
    thickets_ipc[name], tri_ipc[name], cit_ipc[name] = get_tri(df, years)
    print(name + " done")

df_tri_ipc = pd.DataFrame.from_dict(tri_ipc)



#**************
#! PLOTS
#**************
from bokeh.plotting import figure, output_notebook, show 
from bokeh.io import export_png
from bokeh.models import NumeralTickFormatter

output_notebook()

#*figure on absolute number of triples
p_abstrip = tech_plot(years, list(tri_total.values()), list(tri_disc.values()), list(tri_com.values()), 
                    "Total number of triples", "Absolute number of triples")
#p.yaxis.formatter = NumeralTickFormatter(format = "0000")
show(p_abstrip)
#export_png(p_abstrip, filename = "output/abs_triples_tech.png")

#*figure on share of triples relative to total citations
p_share = tech_plot(years, total_share, disc_share, com_share, 
                    "Share of triples realtive to all citations", "Share of triples")
show(p_share)
#export_png(p_share, filename = "output/shares_triples_totalcit")

#* shares by ipc 
ticks = [(x, y) for x, y in zip(df_2["field_num"], df_2["field"])]
ticks = list(dict.fromkeys(ticks))
ticks = dict(ticks)

p_ipc = figure(plot_width = 500, plot_height = 500, x_axis_label = "Technology Field", 
                y_axis_label = "Percentage share", title = "IPC Shares")
p_ipc.vbar(x = field_nums, top = ipc_shares, width = 0.9)
p.xaxis.ticker = list(ticks.keys())
p_ipc.xaxis.major_label_overrides = ticks
p_ipc.xaxis.major_label_orientation = 0.8
show(p_ipc)



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

