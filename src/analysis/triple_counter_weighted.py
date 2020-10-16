import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.cluster import _directed_triangles_and_degree_iter
import os
from bokeh.plotting import figure, show, output_notebook
from itertools import chain
import itertools
import time
import collections

#set up path
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

#*##########################
#!FUNCTIONS
#*##########################

def get_nodes(df, nodescol = "nodes"):
    """
    Get nodes from df containing nodes info.

    *df = df with info on nodes
    *nodescol = column containing nodes
    """
    nodes = df[nodescol].tolist()
    return(nodes)

def get_edges(df, edgescol = "srcdst"):
    """
    Get edges from df containing info on edges. Necessary that df contains
    includes col with edges as tuple and as single columns.

    *df = df containing info on edges
    *edgescol = column containing edges as tuples
    """
    df["count"] = df.groupby([edgescol]).cumcount() + 1
    df["edges"] = [(u, v, k) for u, v, k in zip(df_3["firm_src"], df_3["firm_dst"], df_3["count"])]
    edges = df["edges"].tolist()
    return(edges)

def get_edgeattrs(df, *args):
    """
    Get attributes of edges from df containing info on edges. Some are pre-specified,
    more can be added using *args.

    *df = df containing info on edges
    **args = further attributes
    """
    df_edges = df.set_index("edges")
    df_edges = df_edges[["field_num", "sector", "technology", "year", "weights", "count", *args]]
    attr_edges = df_edges.to_dict(orient = "index")
    return(attr_edges)

def get_nodeattrs(df, nodescol = "nodes", *args):
    """
    Get attributes of nodes from df containing info on nodes. Some are pre-soecified,
    more can be added using *args.

    *df = df containing info on nodes
    *nodescol = column containing nodes
    **args = further attributes
    """
    df_nodes = df.set_index(nodescol)
    df_nodes = df_nodes[["year", "field_num", "sector", "technology", *args]]
    attr_nodes = df_nodes.to_dict(orient = "index")
    return(attr_nodes)

def setup_G(df_edges, df_nodes):
    """
    Sets up a NetworkX.MultiDiGraph(), with nodes from df_nodes
    and edges from df_edges. Attributes are added for respective element using
    info contained in respective df.

    df_edges = df containing info on edges
    df_nodes = df containing info on nodes.
    """
    nodes = get_nodes(df_nodes)
    print("got nodes")
    #node_attrs = get_nodeattrs(df_nodes)
    #print("got node attributes")
    edges = get_edges(df_edges)
    df_edges["edges"] = edges
    print("got edges")
    edge_attrs = get_edgeattrs(df_edges)
    print("got edge attributes")
    G = nx.MultiDiGraph()
    G.add_nodes_from(nodes)
    print("nodes added")
    #nx.set_node_attributes(G, node_attrs)
    #print("node attributes added")
    G.add_edges_from(edges)
    print("edges added")
    nx.set_edge_attributes(G, edge_attrs)
    print("edges attributes added")
    return(G)

#below not usable for multigraph so far
def mutuals(G, weights = True):
    """
    A function to find the list of nodes that are successors as well as
    predecessors of node n in a NetworkX.DiGraph().
    This is done for all nodes and dictionary returned is structured as
    {node: list of nodes that are predec and succec, node2: ...}
    G: directed Networkx Graph
    """
    if weights == True:
        node_dict = {}
        weights_dict = {}
        nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter(nodes))
        for i, preds, succs in nbrs:
            both_dir = []
            for y in preds:
                if y in succs:
                    both_dir.append(y)
                    weights_dict[(i, y)] = (G[i][y]["weight"])
            node_dict[i] = both_dir
        return(node_dict, weights_dict)
    else:
        node_dict = {}
        nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter(nodes))
        for i, preds, succs in nbrs:
            both_dir = []
            for y in preds:
                if y in succs:
                    both_dir.append(y)
            node_dict[i] = both_dir
        return(node_dict)

def gettris_di(G):
    """
    Gets a list of lists containing triangles existing in NetworkX.DiGraph().
    Mostly based on _directed_triangles_and_degree_iter from NetworkX.

    *G = NetworkX.DiGraph()
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
    k.sort()
    fin = list(k for k,_ in itertools.groupby(k))
    return(fin)

def gettris(G):
    """
    Gets a list of lists of triangles existing in NetworkX.Graph().

    *G = NetworkX.Graph()
    """
    alltris = []
    tridict = {}
    if nodes is None:
        nodes_nbrs = G.adj.items()
    else:
        nodes_nbrs = ((n, G[n]) for n in G.nbunch_iter(nodes))
    for v, v_nbrs in nodes_nbrs:
        vs = set(v_nbrs) - {v}
        for j in vs:
            jnbrs = set(G.adj[j]) - {j}
            both = list(jnbrs.intersection(vs))
            both = list(dict.fromkeys(both))
            tridict[(v, j)] = both
    for j, x in tridict.items():
        for i in x:
            alltris.append(sorted((j[0], j[1], i)))
    k = alltris
    k.sort()
    fin = list(k for k,_ in itertools.groupby(k))
    return(fin)

def getthicket(G, tris, weight = "weight"):
    """
    Follow-up funtion to gettris. Use list of triangles to get weights and add up
    """
    weight_sums = {}
    for x in tris:
        w1 = G[x[0]][x[1]][weight]
        w2 = G[x[0]][x[2]][weight]
        w3 = G[x[1]][x[2]][weight]
        weight_sums[(x[0], x[1], x[2])] = np.sum((w1, w2, w3))
    thicket = np.sum(list(weight_sums.values()))
    return(weight_sums, thicket)

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
    triple counting when using all nodes)
    - additionally, when looking at source code from _directed_triangles_and_degree_iter we see that for each triangle
    4 counters are added since the by mutual() filtered graph fulfills all the conditions anytime
    - hence, in total need to divide by 24 to get same number of triangles as in undirected graph
"""

#*##########################
#!DATA
#*##########################

df_2 = pd.read_csv("data/df2.csv")
df_3 = pd.read_csv("data/df3.csv")
df_4 = pd.read_csv("data/df4.csv")

grant_grant = pd.read_csv("data/grant_grant.csv")
type(grant_grant.loc[0, "patnum"])
#*##########################
#!GRAPH
#*##########################

#changing the setup of the analysis:
#instead of filtering the data and tehn creating a graph, I will
#create a graph with all edges and include metadata for filtering

#create dummy weights
df_3["weights"] = np.random.rand(len(df_3))

#set up graph environment
nodes = get_nodes(df_3)
G = setup_G(df_3, nodes)

#add all edges
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
    print(year)

#get node_dict of mutual edges
node_dict = mutuals(G)

#cretae DIRECTED graph out of above received node_dict
G_di = nx.DiGraph(node_dict)

#get directed triangles
trisdi = ditriangles(G_di)
trissum = np.sum(list(trisdi.values()))/24 #see notes why divided by 24

#get a list of the nodes involved in each triangle
trifin = gettris(G_di)

#*##########################
#!GRAPH (weighted)
#*##########################
#set up graph environment
Gw = nx.DiGraph()
#add nodes
Gw.add_nodes_from(nodes)

#add all edges
df = df_3
df["weights"] = np.random.rand(len(df))
years = np.arange(1976, 2001)
thickets = {}
for year in years:
    """
    this loop:
        - gets data for respective year
        - adds citations from this year as edges to G
        - makes neighbor analysis
        - creates a new graph only with nodes that have mutually directed edges
        - counts triangles and fills up initialized dicts
    """
    year = 1976
    matched_year = df[df['year'] == year]
    #matched_year = matched_year[matched_year['firm_src'] != matched_year['firm_dst']]
    citations = len(df_2[df_2["year"] == year])
    #add edges
    edges = list(zip(matched_year['firm_src'], matched_year['firm_dst'], matched_year["weights"]))
    #right now: if same edge appears > 1 then the weight is updated every time edge appears
    #since the duplicates are also relying on the weight
    edges = list(set([i for i in edges]))
    Gw.add_weighted_edges_from(edges)
    node_dict_w, weights_dict = mutuals(Gw, weights = True)
    Gw_sub = nx.Graph(node_dict_w)
    if len(list(Gw_sub.edges())) == 0:
        print(year)
    else:
        Gw_sub = nx.set_edge_attributes(Gw_sub, weights_dict, name = "weight")
        tris = gettris(Gw_sub)
        thickets[year] = getthicket(Gw_sub, tris)[1]
        print(year)
