import numpy as np
import pandas as pd
import networkx as nx
import os
from collections import Counter

#!set up directory
#add path to project
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_lc)
#adjusting print settings for Python
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
    nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter(nodes))
    for i, preds, succs in nbrs:
        both_dir = []
        for y in preds:
            if y in succs:
                both_dir.append(y)
        node_dict[i] = both_dir
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
        print(year)
    return(thicket_dict, tri_dict, cit_dict)

def tech_plot(x, total, disc, com, title, ylab, xlab = "Year"):
    """
    Function to create plots with total, discrete and complex data.
    """
    plot = figure(plot_width = 500, plot_height = 500, x_axis_label = xlab,
                y_axis_label = ylab, title = title)
    plot.line(x, total, color = "blue", legend_label = "total")
    plot.line(x, disc, color = "red", legend_label = "discrete")
    plot.line(x, com, color = "orange", legend_label = "complex")
    plot.legend.location = "top_left"
    return(plot)

def barplot(top, title, ylab, x, ticks, xlab = "Technology Field"):
    """
    Create vbarplots for share of citations across fields in different variations.
    """
    plot = figure(plot_width = 500, plot_height = 500,
                title = title,
                x_axis_label = xlab, y_axis_label = ylab)
    plot.vbar(x = x, top = top, width = 0.9)
    plot.xaxis.ticker = list(ticks.keys())
    plot.xaxis.major_label_overrides = ticks
    plot.xaxis.major_label_orientation = 0.8
    return(plot)


#**************
#! DATA
#**************
df_full = pd.read_csv("data/df1.csv")
df_2 = pd.read_csv("data/df2.csv")
df_3 = pd.read_csv("data/df3.csv")
df_4 = pd.read_csv("data/df4.csv")
df_disc = df_3[df_3["technology"] == "discrete"]
df_com = df_3[df_3["technology"] == "complex"]

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

thickets_all = pd.DataFrame.from_dict(thicket_dict_all)
tri_all = pd.DataFrame.from_dict(tri_dict_all)
cit_all = pd.DataFrame.from_dict(cit_dict_all)

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
    df = df_3[df_3["field_num"] == field[0]]
    name = field[1]
    thickets_ipc[name], tri_ipc[name], cit_ipc[name] = get_tri(df, years)
    print(name + " done")

df_tri_ipc = pd.DataFrame.from_dict(tri_ipc)
df_cit_ipc = pd.DataFrame.from_dict(cit_ipc)
df_thicket_ipc = pd.DataFrame.from_dict(thickets_ipc)


#**************
#! PLOTS
#**************
from bokeh.plotting import figure, output_notebook, show
from bokeh.io import export_png
from bokeh.models import NumeralTickFormatter

output_notebook()

#* figure on absolute number of triples
p_abstrip = tech_plot(years, tri_all["total"], tri_all["discrete"], tri_all["complex"],
                    "Total number of triples", "Absolute number of triples")
#p.yaxis.formatter = NumeralTickFormatter(format = "0000")
show(p_abstrip)
#export_png(p_abstrip, filename = "output/documentation/Week33/abs_triples_tech.png")

#* figure on share of triples relative to total citations
p_share = tech_plot(years, thickets_all["total"], thickets_all["discrete"], thickets_all["complex"],
                    "Share of triples realtive to all citations", "Share of triples")
show(p_share)
#export_png(p_share, filename = "output/documentation/Week33/shares_triples_totalcit.png")

#* shares by ipc
ticks = [(x, y) for x, y in zip(df_2["field_num"], df_2["field"])]
ticks = list(dict.fromkeys(ticks))
ticks = dict(ticks)

ipc_shares = df_tri_ipc.loc["2000", :]/df_tri_ipc.loc["2000", :].sum()

p_ipc = barplot(top = ipc_shares, title = "IPC Shares", ylab = "Percentage share". ticks = ticks, x = field_nums)
show(p_ipc)
#export_png(p_ipc, filename = "output/documentation/Week33/ipc_shares.png")

#* citations per field
df2_count = df_2.groupby("field_num").count()
counter = df2_count["year"]

p_cit = barplot(top = counter, title = "Total citations per field in df2", ylab = "Absolute Number", ticks = ticks, x = field_nums)
show(p_cit)
#export_png(p_cit, filename = "output/documentation/Week33/cit_numbers.png")

#* share of citation per field relative to all citations
df2_shares = df2_count["year"]/len(df_2)

p_citshare = barplot(top = df2_shares, title = "Share of citations per field relative to total citations", ylab = "Percentage Share", ticks = ticks, x = field_nums)
show(p_citshare)
#export_png(p_citshare, filename = "output/documentation/Week33/cit_shares.png")
