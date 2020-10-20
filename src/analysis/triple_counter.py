import numpy as np
import pandas as pd
import networkx as nx
import os
from collections import Counter
import itertools
import ast

#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "/Users/christianhilscher/Desktop/tmtc/"
os.chdir(wd_lc)

np.set_printoptions(suppress=True)

#**************
#! FUNCTIONS
#**************

def setup_G(df, src, dst):
    """
    Set up a NetworkX.DiGraph() with nodes being unique elements of src and dst columns 
    of df combined. 
    *df: dataframe containing edge pairs 
    *src: string, column of source of edge
    *dst: string, column of destination of edge
    
    return: NetworkX.DiGraph()
    """
    #set up empty graph
    G = nx.DiGraph() 
    #get unique nodes
    nodes = df[src].append(df[dst]).drop_duplicates().tolist()
    #add nodes to graph
    G.add_nodes_from(nodes)
    return(G)

def setup_G_edges(df, G, years, edgecol = "srcdst"): 
    """
    Add edges to NetworkX.DiGraph() returned by setup_G. 
    Used to get complete graph including all edges.
    
    *df: dataframe 
    *years: list of years 
    
    returns: NetworkX.DiGraph()
    """
    edges = df[edgecol].tolist()
    G.add_edges_from(edges)
    return(G)

def mutuals(G):
    """
    Find the list of nodes that are successors as well as predecessors of node n 
    in a Networkx.DiGraph(). This is done for all nodes. Nodes that do not have any 
    nodes that are predecessors as well as successors as are deleted.
    
    G: Networkx.DiGraph() 
    
    return: dictionary structured as {node1: list of neighbor and predec nodes, node2: ...}
    """
    nodes = G.nodes()
    node_dict = {}
    nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter(nodes))
    for i, preds, succs in nbrs:
        both_dir = []
        for y in preds:
            if y in succs:
                both_dir.append(y)
        node_dict[i] = both_dir
    for k, v in list(node_dict.items()):
        if v == []:
            del node_dict[k]
    return(node_dict)

def filter_tech(df, tech):
    """
    Filter edges_df for discrete, complex or mixed citation pairs.
    
    *df: edges dataframe
    *tech: technology string marking column
    
    return: tech_df, dataframe only containing entries belonging to tech
    """
    tech_df = df[df[tech] == True]
    return(tech_df)

def mutdf(df, node_dict):
    """
    Filter edges dataframe for entries that only inlcude firms that are in graph that results
    from applying mutuals(G). 
    
    #!I DON'T KNOW WHETHER THIS IS THE DENOMINATOR WE WANT, IF SO ADJUST IN tris_and_cits()
    
    """
    firms = []
    for k, v in node_dict.items(): 
        firms.append(k)
        for i in v: 
            firms.append(i)
    #remove duplicates
    firms = list(dict.fromkeys(firms))
    #filter df 
    mutdf = df[df["firm_src"].isin(firms) | df["firm_dst"].isin(firms)]
    return(mutdf)

def get_tri(G):
    """
    Get total number of triangles in G. 
    See Networkx.triangles doc for why divided by 3.
    
    G: Networkx.Graph() 
    
    return: integer number of total triangles
    """
    tris = np.sum(list(nx.triangles(G).values()))/3
    return(tris)

def tris_and_cits(df, G_di, years, edgecol = "srcdst"):
    """
    Function that binds all other functions to count total patent citations and
    triangles for all years supplied. 
    
    #*df: dataframe containing info on edges
    #*G: initial NetworkX.DiGraph() that edges are added to
    #*years: iterable of years of interest
    #*edgecol: column containing tuples of edges (src, dst)
    
    returns: 2 dictionaries containing number of citations and triangles structured as 
    {year: value}.
    
    Note: thickets are not returned automatically since denominator of total citations for thicket 
    is not necessarily number of total citations returned here. See README. 
    """
    #set up counter for total citations 
    tot_cit = 0 
    #initialize empty dictionaries that will be filled 
    cit_dict = {}
    tri_dict = {}
    #loop over years 
    for i in years:
        """
        this loop:
            - gets data for respective year
            - adds citations from this year as edges to G
            - makes neighbor analysis using mutuals(G)
            - creates a new graph only with nodes that have mutually directed edges
            - counts triangles and fills up initialized dicts
        """
        #get data of interest for respective year 
        doi = df[df["year_src"] == i]
        #get number of ctiations in this year (len(doi)) and add to count 
        tot_cit = len(doi) + tot_cit
        #get edges 
        edges = doi[edgecol].tolist()
        #add edges to directed graph; note: not a multigraph, same edge that appears multiple times only added once
        G_di.add_edges_from(edges)
        #now get undirected graph 
        mutualnodes = mutuals(G)
        G_undi = nx.Graph(mutualnodes)
        #count triangles 
        tris = get_tri(G_undi)
        #add everything to dictionaries 
        tri_dict[i] = tris 
        cit_dict[i] = tot_cit
        print(i)
    return(tri_dict, cit_dict)

def get_thicket(tris, cits, years): 
    """
    Given dictionaries returned by tris_and_cits calculate thicket for each year. 
    
    *tris: dictionary of triangles by year
    *cits: dictionary of citations by year 
    *years: iterable of years of interest
    
    return: thicket = # of triangles/# of total citations 
    """
    thickets = {i: tris[i]/cits[i] for i in years}
    return(thickets)

def get_trilist(G_undi, nodes = None):
    """
    Gets a list of lists of triangles existing in NetworkX.Graph() G.
    
    *G = NetworkX.Graph()
    
    returns: list of lists containing firm numbers, inner list forming a triangle
    """
    alltris = []
    tridict = {}
    nodes = None
    if nodes is None:
        nodes_nbrs = G_undi.adj.items()
    else:
        nodes_nbrs = ((n, G_undi[n]) for n in G_undi.nbunch_iter(nodes))
    for v, v_nbrs in nodes_nbrs:
        vs = set(v_nbrs) - {v}
        for j in vs:
            jnbrs = set(G_undi.adj[j]) - {j}
            both = list(jnbrs.intersection(vs))
            tridict[(v, j)] = both
    for j, x in tridict.items():
        for i in x:
            alltris.append(sorted((j[0], j[1], i)))
    k = alltris 
    k.sort()
    fin = list(k for k,_ in itertools.groupby(k))
    return(fin)

def get_weights(df, srcdstcol = "srcdst"):
    #sort tuples to count all edges between two firms for weighting
    df["srcdst_sort"] = df[srcdstcol].apply(sorted).apply(tuple)
    #create a dataframe containing the weights 
    weights = df.groupby("srcdst_sort").count().reset_index()
    weights = weights.rename(columns = {"srcdst_sort": "edge", "src": "connections"})[["edge", "connections"]]
    return(weights)

def get_triedges(trilist):
    triedges = {}
    for i in trilist:
        triedges[i] = list(itertools.combinations(i, 2))
    return(triedges)

def get_triedges_df(triedges):     
    triedges_df = pd.DataFrame.from_dict(triedges, orient = "index")
    triedges_df["edges"] = triedges_df.values.tolist()
    return(triedges_df)

def tricount(triedges_df, weights_df, colnums = 3):     
    #now merge based on each edge with weights dataframe
    for i in range(0, colnums): 
        triedges_df = triedges_df.merge(weights_df, left_on = i, right_on = "edge", how = "left", indicator = True)
        triedges_df = triedges_df.drop(["_merge", "edge"], axis = 1)
    triedges_df["values"] = triedges_df.iloc[:, 4:7].sum(axis = 1)
    values = triedges_df["values"].tolist()
    return(values)

def triangles_edgecount(edges_df, G_di, years, edgecol = "srcdst"):
    tris = {}
    tri_counted = 0
    for i in years: 
        doi = edges_df[edges_df["year_src"] == i]
        doi_weights = edges_df[edges_df["year_src"] <= i]
        weights = get_weights(doi_weights)
        edges = doi[edgecol].tolist()
        G_di.add_edges_from(edges)
        G_undi = nx.Graph(mutuals(G_di))
        trilist = get_trilist(G_undi)
        trilist = map(tuple, trilist)
        triedges = get_triedges(trilist)
        triedges_df = get_triedges_df(triedges)
        if len(triedges_df) != 0:
            tri_counted = np.sum(tricount(triedges_df, weights)) #+ tri_counted
            tris[i] = tri_counted
            print(i, tris[i], sep = ":")
        else:
            tris[i] = 0
    return(tris)

#**************
#! DATA
#**************

edges_df = pd.read_csv("data/df3 3.csv")
edges_df["srcdst"] = edges_df["srcdst"].apply(ast.literal_eval)
#* add identifier for technology 
edges_df["complex"] = (edges_df["technology_src"] == "complex") & (edges_df["technology_dst"] == "complex")
edges_df["discrete"] = (edges_df["technology_src"] == "discrete") & (edges_df["technology_dst"] == "discrete")
edges_df["mixed"] = (edges_df["complex"] == False) & (edges_df["discrete"] == False)

#* filter for 15 year expiration 
active = edges_df[edges_df["year_src"] - edges_df["year_dst"] < 15]

#**************
#! NETWORK
#**************

#* set up Graph 
years = range(1976, 2001)
G = setup_G(active, "firm_src", "firm_dst")

#* Total
#* get triangles and citations of all patents
tris, cits = tris_and_cits(active, G, years)
thicket = get_thicket(tris, cits, years)

#* complex tech triangles and citations 
com_df = filter_tech(active, "complex")
G.remove_edges_from(list(G.edges))
tricom, citcom = tris_and_cits(com_df, G, years)
thicketcom = get_thicket(tricom, cits, years)

#* discrete tech triangles and citations 
disc_df = filter_tech(active, "discrete")
G.remove_edges_from(list(G.edges))
tridisc, citdisc = tris_and_cits(disc_df, G, years)
thicketdisc = get_thicket(tridisc, cits, years)

#* triangles counted by using ocurrence of each edge as a weight    
years = range(1976, 2001)
G = setup_G(active, "firm_src", "firm_dst")
triangles_edge_counted = triangles_edgecount(active, G, years = years)
triangles_edge = pd.DataFrame({"year": list(triangles_edge_counted.keys()), 
                            "values": list(triangles_edge_counted.values())})


#!Save data 
#get into frame 
techs = ["complete", "complex", "discrete"]
triall = {}
citsall = {}
thicketall = {}
for i, j in zip(techs, [tris, tricom, tridisc]): 
    triall[i] = j
for i, j in zip(techs, [cits, citcom, citdisc]):
    citsall[i] = j
for i, j in zip(techs, [thicket, thicketcom, thicketdisc]): 
    thicketall[i] = j

thicketdf = pd.DataFrame.from_dict(thicketall)
tridf = pd.DataFrame.from_dict(triall)
citdf = pd.DataFrame.from_dict(citsall)

thicketdf.to_csv("output/tmp/thickets.csv")
tridf.to_csv("output/tmp/tris.csv")
citdf.to_csv("output/tmp/cits.csv")