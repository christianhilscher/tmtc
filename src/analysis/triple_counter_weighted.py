import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.cluster import _directed_triangles_and_degree_iter
import os
from bokeh.plotting import figure, show, output_notebook, from_networkx
from itertools import chain
import itertools
import time
import collections
import ast

#set up path
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

###########################
#! FUNCTIONS
###########################
def get_first(num):
    first = float(str(num)[:4])
    return(first)

def get_nodes(df, nodescol = "firm"):
    """
    Get nodes from df containing nodes info.

    *df = df with info on nodes
    *srccol = column containing source firms
    *dstcol = column containing destination firms
    """
    nodes = df[nodescol].drop_duplicates().to_list()
    return(nodes)

def get_nodeattrs(nodes_df, nodes, nodescol = "firm"):
    """
    Gets the node attributes as necessary (as a dict of dict of dict). See Readme
    for more info/add better docstring.
    """
    node_dict = {}
    for i in nodes:
        sub_df = nodes_df[nodes_df[nodescol] == i].set_index("patnum").drop(nodescol, axis = 1)
        node_dict[i] = sub_df.to_dict(orient = "index")
    return(node_dict)

def get_edges(df, src = "firm_src", dst = "firm_dst", edgescol = "srcdst"):
    """
    Get edges from df containing info on edges. Necessary that df contains
    includes col with edges as tuple and as single columns.

    *df = df containing info on edges
    *src = source of citation (start of edge)
    *dst = destination of citation (end of edge)
    *edgescol = column containing edges as tuples
    """
    df["count"] = df.groupby([edgescol]).cumcount() + 1
    df["edges"] = [(u, v, k) for u, v, k in zip(df[src], df[dst], df["count"])]
    edges = df["edges"].tolist()
    return(edges)

def get_edgeattrs_multi(df, *args):
    """
    Get attributes of edges from df containing info on edges. Some are pre-specified,
    more can be added using *args.

    *df = df containing info on edges
    **args = further attributes
    """
    df_edges = df.set_index("edges")
    df_edges = df_edges[["count", "weights", "owner", "year", "patents", "category", "subcategory", *args]]
    attr_edges = df_edges.to_dict(orient = "index")
    return(attr_edges)

def get_edgeattrs_single(multiG):
    edge_dict = {}
    for u, v in multiG.edges():
        edge_dict[(u, v)] = {}
    for u, v, k, d in multiG.edges(data = True, keys = True):
        edge_dict[(u, v)][k] = d
    for x in edge_dict.keys():
        subdict = edge_dict[x]
        weight = 0
        for i in subdict:
            weight = weight + subdict[i]["weights"]
        edge_dict[x]["weight"] = weight
    return(edge_dict)

def setup_G(df_nodes, df_edges):
    """
    Set up a NetworkX.MultiDiGraph(), assign attributes to multiple edges,
    get edge attributes as described in README/more detailed description will follow.
    """
    nodes = get_nodes(df_nodes)
    print("got nodes")
    nodes_attrs = get_nodeattrs(df_nodes, nodes)
    print("got node attrs")
    edges = get_edges(df_edges)
    df_edges["edges"] = edges
    print("got edges")
    edge_attrs = get_edgeattrs_multi(df_edges)
    print("got edge attrs")
    #create multigraph to assign edge attributes
    multi = nx.MultiDiGraph()
    #nodes
    multi.add_nodes_from(nodes)
    nx.set_node_attributes(multi, nodes_attrs)
    print("nodes done")
    multi.add_edges_from(edges)
    nx.set_edge_attributes(multi, edge_attrs)
    print("edges done")
    edge_single_attrs = get_edgeattrs_single(multi)
    print("single attrs done")
    single = nx.DiGraph()
    single.add_nodes_from(nodes)
    nx.set_node_attributes(single, nodes_attrs)
    print("nodes single done")
    edges = [(i[0], i[1]) for i in edges]
    single.add_edges_from(edges)
    nx.set_edge_attributes(single, edge_single_attrs)
    print("edges single done")
    return(single)

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
        nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter())
        for i, preds, succs in nbrs:
            both_dir = []
            for y in preds:
                if y in succs:
                    both_dir.append(y)
                    weights_dict[(i, y)] = G.get_edge_data(i, y)
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

def ditriangles(G, nodes = None):
    """
    Implement triangles count for directed graphs as well.
    Basically copying triangles function for undirected graphs from NetworkX
    """
    if nodes in G:
        return next(_directed_triangles_and_degree_iter(G, nodes))[3] // 2
    return {n: t // 2 for n, td, rd, t in _directed_triangles_and_degree_iter(G, nodes)}

def filterG_nodes(G, attr, val, equal = "equal"):
    nodes = []
    for n, d in G.nodes(data = True):
        for k, v in d.items():
            if equal == True:
                if v[attr] == val:
                    nodes.append(n)
            elif equal == "leq":
                if v[attr] <= val:
                    nodes.append(n)
            elif equal == "geq":
                if v[attr] >= val:
                    nodes.append(n)
    subgraph = G.subgraph(nodes)
    return(subgraph)

def filterG_edges(Gtot, attr, pair):
    """
    Filter subgraph from graph based on attribute and pair described, e.g. (year, year) or (complex, complex)
    which will be technology complex.
    """
    edges = Gtot.edges(data = True)
    filtered = []
    for u, v, d in edges:
        d.pop("weight")
        for k, val in d.items():
            if val[attr] == pair:
                filtered.append((u, v))
    sub = Gtot.edge_subgraph(filtered)
    return(sub)

def getthicket(G, years):
    """
    - Calculate thicket based on
    thicket = (# of triangles)/(# of edges in Graph)
    - note: Graph is result of mutuals(G)
    """
    trianglesdict = {}
    citations = {}
    thickets = {}
    #first, filter graph by year
    for x in years:
        subgraph = filterG_nodes(G, "year", x, equal = "leq")
        tris = list(nx.triangles(G).values())
        tris = np.array(tris)
        tris = np.sum(tris)/3
        cit = subgraph.number_of_edges()
        thickets[x] = cit/tris
        trianglesdict[x] = tris
        citations[x] = cit
        print(str(x) + " done")
    return(thickets, triangles, citations)

def getthicket2(G):
    """
    Get thicket using weights
    """
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

###########################
#! DATA
###########################

nodes_df = pd.read_csv("output/tmp/nodesdata.csv")
edges_df = pd.read_csv("output/tmp/edgesdata.csv")

df_3 = pd.read_csv("data/df3 2.csv")
tech = pd.read_csv("data/ipcs.csv")
tech = tech.drop_duplicates(["ipc_code"])
tech = tech[["ipc_code", "technology"]]

df_3["weights"] = np.random.rand(len(df_3))
edges = []
for i in df_3["srcdst"]:
    edges.append(ast.literal_eval(i))
df_3["srcdst"] = edges
df_3["firm_src"] = df_3["firm_src"].astype("int")
df_3["firm_dst"] = df_3["firm_dst"].astype("int")
#general information
grant_grant = pd.read_csv("data/grant_grant.csv")
grant_grant["patnum"] = grant_grant["patnum"].astype("str")
grant_grant = grant_grant.drop("Unnamed: 0", axis = 1)
#patentsview nber classification
nber = pd.read_csv("data/patentsview/nber.tsv", sep = "\t")
nber = nber.drop("uuid", axis = 1)

#create nodes dataframe
#first: get all patents
firm_src = pd.DataFrame(df_3[["firm_src", "patnum"]])
firm_src = firm_src.rename(columns = {"firm_src": "firm"})
firm_dst = pd.DataFrame(df_3[["firm_dst", "dst"]])
firm_dst = firm_dst.rename(columns = {"firm_dst": "firm", "dst": "patnum"})
firmspats = firm_src.append(firm_dst).reset_index()
firmspats["patnum"] = firmspats["patnum"].astype("str")
firmspats = firmspats.merge(grant_grant, left_on = "patnum", right_on = "patnum", how = "left")
firmspats["year"] = firmspats["pubdate"].apply(get_first)
firmspats = firmspats.drop(["ipc", "ipcver", "appdate", "appnum", "pubdate", "title", "abstract", "gen", "file", "index"], axis = 1)
firmspats = firmspats.merge(nber, left_on = "patnum", right_on = "patent_id")
firmspats = firmspats.drop("patent_id", axis = 1)
nodes_df = firmspats.drop_duplicates(subset = ["patnum"])
nodes_df["firm"] = nodes_df["firm"].astype(float)
nodes_df.to_csv("output/tmp/nodesdata.csv")

#edges !
edges = df_3
edges["dst"] = edges["dst"].astype("str")
edges["patnum"] = edges["patnum"].astype("str")
edges = edges[["firm_src", "firm_dst", "dst", "year", "weights", "field_num", "patnum", "srcdst"]]


grant_grant["ipc"] = grant_grant["ipc"].astype(str)
grant_grant["ipc"] = grant_grant["ipc"].apply(lambda x: x[:4])
edges = edges.merge(grant_grant, left_on = "patnum", right_on = "patnum")
edges = edges.merge(grant_grant, left_on = "dst", right_on = "patnum")
edges = edges.merge(tech, left_on = "ipc_x", right_on = "ipc_code")
edges = edges.merge(tech, left_on = "ipc_y", right_on = "ipc_code")
edges = edges.merge(nber, left_on = "patnum_x", right_on = "patent_id")
edges = edges.merge(nber, left_on = "dst", right_on = "patent_id")
edges["year_x"] = edges["pubdate_x"].apply(get_first)
edges["year_y"] = edges["pubdate_y"].apply(get_first)
edges["category"] = [(x, y) for x, y in zip(edges["category_id_x"], edges["category_id_y"])]
edges["subcategory"] = [(x, y) for x, y in zip(edges["subcategory_id_x"], edges["subcategory_id_y"])]
edges["owner"] = [(x, y) for x, y in zip(edges["owner_x"], edges["owner_y"])]
edges["year"] = [(x, y) for x, y in zip(edges["year_x"], edges["year_y"])]
edges["patents"] = [(x, y) for x, y in zip(edges["patnum_x"], edges["dst"])]
edges["technology"] = [(x, y) for x, y in zip(edges["technology_x"], edges["technology_y"])]
edges = edges[["firm_src", "firm_dst", "weights", "owner", "year", "patents", "category", "subcategory", "srcdst", "technology"]]
edges_df = edges
edges_df["firm_src"] = edges_df["firm_src"].astype(float)
edges_df["firm_dst"] = edges_df["firm_dst"].astype(float)
edges_df.to_csv("output/tmp/edgesdata.csv")

###########################
#! GRAPH
###########################

#changing the setup of the analysis:
#instead of filtering the data and then creating a graph, I will
#create a graph with all edges and include metadata for filtering
tick = time.time()
G = setup_G(nodes_df, edges_df)
tock = time.time()
print(tock - tick)

###########################
#! FILTERING GRAPH
###########################

def filterG_nodes(G, attr, val, equal = "equal"):
    nodes = []
    for n, d in G.nodes(data = True):
        for k, v in d.items():
            if equal == True:
                if v[attr] == val:
                    nodes.append(n)
            elif equal == "leq":
                if v[attr] <= val:
                    nodes.append(n)
            elif equal == "geq":
                if v[attr] >= val:
                    nodes.append(n)
    subgraph = G.subgraph(nodes)
    return(subgraph)

def filterG_edges(Gtot, attr, pair):
    """
    Filter subgraph from graph based on attribute and pair described, e.g. (year, year) or (complex, complex)
    which will be technology complex.
    """
    edges = Gtot.edges(data = True)
    filtered = []
    for u, v, d in edges:
        d.pop("weight")
        for k, val in d.items():
            if val[attr] == pair:
                filtered.append((u, v))
    sub = Gtot.edge_subgraph(filtered)
    return(sub)

df = edges_df
for i in range(len(df)): 
    year = df.loc[i, "year"]
    if year[0] - year[1] > 15: 
        df.drop(i)
    print(i)

def getthicket(G, years):
    """
    - Calculate thicket based on
    thicket = (# of triangles)/(# of edges in Graph)
    - note: Graph is result of mutuals(G)
    """
    trianglesdict = {}
    citations = {}
    thickets = {}
    #first, filter graph by year
    for x in years:
        subgraph = filterG_nodes(G, "year", x, equal = "leq")
        tris = list(nx.triangles(G).values())
        tris = np.array(tris)
        tris = np.sum(tris)/3
        cit = subgraph.number_of_edges()
        thickets[x] = cit/tris
        trianglesdict[x] = tris
        citations[x] = cit
        print(str(x) + " done")
    return(thickets, triangles, citations)
