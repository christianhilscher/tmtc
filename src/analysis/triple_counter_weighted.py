import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.cluster import _directed_triangles_and_degree_iter
import os
from bokeh.plotting import figure, show, output_notebook
from itertools import chain
import itertools

#set up path
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

###########################
#FUNCTIONS
###########################
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

def gettris(G):
    """
    Add description - mostly based on _directed_triangles_and_degree_iter
    Returns a list of lists where inner level contains nodes that form a triangle
    """
    tridict = {}
    alltris = []
    nodes_nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter(nodes))
    for i, preds, succs in nodes_nbrs:
        ipreds = set(preds) - {i}
        isuccs = set(succs) - {i}
        for j in chain(ipreds, isuccs):
            jpreds = set(G._pred[j]) - {j}
            jsuccs = set(G._succ[j]) - {j}
            predspreds = list(jpreds.intersection(ipreds))
            succsucc = list(jsuccs.intersection(isuccs))
            predssucc = list(jpreds.intersection(isuccs))
            succpreds = list(jsuccs.intersection(ipreds))
            joint = predspreds + succsucc + predssucc + succpreds
            joint = list(dict.fromkeys(joint))
            tridict[(i, j)] = joint
    for j, x in zip(tridict.keys(), tridict.values()):
        for i in x:
            alltris.append(sorted((j[0], j[1], i)))
    k = alltris
    trifin = k.sort()
    trifin = list(k for k,_ in itertools.groupby(k))
    return(trifin)

def ditriangles(G, nodes = None):
    """
    Implement triangles count for directed graphs as well.
    Basically copying triangles function for undirected graphs from NetworkX
    """
    if nodes in G:
        return next(_directed_triangles_and_degree_iter(G, nodes))[3] // 2
    return {n: t // 2 for n, td, rd, t in _directed_triangles_and_degree_iter(G, nodes)}

"""
Notes:
    - when first doing filtering using mutuals(), # of edges between directed and undirected graph
    differs by factor of 2 since all edges appear basically twice in directed graph
    - that is why we need to additionally divide the number of total triangles by 2 (additionally to
    the dividing by 2 in the fuction itself due to double counting and the division by three because of the
    triplce counting when using all nodes)
    - additionally, when looking at source code from _directed_triangles_and_degree_iter we see that for each triangle
    4 counters are added since the by mutual() filtered graph fulfills all the conditions
    - hence, in total need to divide by 24 to get same number of triangles as in undirected graph
"""

###########################
#FUNCTIONS
###########################

df_2 = pd.read_csv("data/df2.csv")
df_3 = pd.read_csv("data/df3.csv")
df_4 = pd.read_csv("data/df4.csv")

#set up nodes
nodes = df_3["firm_dst"].append(df_3["firm_src"]).drop_duplicates(keep = "first")
nodes = list(nodes)
#set up graph environment
G = nx.DiGraph()
G.add_nodes_from(nodes)

#add some edges to play around with
df = df_3
years = np.arange(1976, 2001)
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
    #add edges
    edges = list(zip(matched_year['firm_src'], matched_year['firm_dst']))
    edges = list(set([i for i in edges]))
    G.add_edges_from(edges)
#how many actual triangles are there
node_dict = mutuals(G)
G_di = nx.DiGraph(node_dict)
#now try with _directed_triangles_and_degree_iter
#get directed triangles
trisdi = ditriangles(G_di)
trifin = gettris(G_di)
