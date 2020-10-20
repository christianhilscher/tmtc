import numpy as np 
import pandas as pd 
import networkx as nx 
import os 
import itertools 

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)
#*now: new approach to count triangles, namely DeGrazia et al. (2020) method

#use setup_G function from triple_counter.py
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

def setup_G_edges(df, G, edgecol = "srcdst"): 
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

def get_triads(G, nodes = None):
    """
    Get triads as defined in README given a NetworkX.DiGraph().
    
    returns: a list of 3-tuples, where each tuple contains nodes that are part 
    of a triad
    """
    nodes = None
    triads = []
    nbrs = ((n, G._succ[n]) for n in G.nbunch_iter(nodes))
    for k, succs in nbrs:
        #k is a node and succs its successors
        #now loop over all sucessors 
        for j in succs: 
            #remove j from succs for intersection finding 
            succs_noj = set(succs) - {j}
            #now get the successors of this successor node 
            succs_j = set(G._succ[j])
            #and the predecessors 
            preds_j = set(G._pred[j])
            #check the intersection between succs(j) and succs(k)
            succs_inter = succs_j.intersection(succs_noj)
            for x in succs_inter: 
                triads.append((k, j, x))
    number = len(triads)
    return(number, triads)

def getthicket(G, tris, weight = "weight"):
    """
    Follow-up funtion to get_triads. Use list of triangles to get weights and add up
    """
    weight_sums = {}
    for x in tris:
        w1 = G[x[0]][x[1]][weight]
        w2 = G[x[0]][x[2]][weight]
        w3 = G[x[1]][x[2]][weight]
        weight_sums[(x[0], x[1], x[2])] = np.sum((w1, w2, w3))
    thicket = np.sum(list(weight_sums.values()))
    return(weight_sums, thicket)

def triads_and_cits(df, G_di, years, edgecol = "srcdstpats"):
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
    triads_dict = {}
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
        #count triangles 
        tris, triads = get_triads(G_di)
        #add everything to dictionaries 
        tri_dict[i] = tris 
        triads_dict[i] = triads
        cit_dict[i] = tot_cit
        print(i)
    return(tri_dict, cit_dict, triads_dict)

#**************
#! DATA
#**************
df3post2000 = pd.read_csv("data/df3to2020.csv")
df3pre2000 = pd.read_csv("data/df3 3.csv")
df3 = pd.read_csv("data/df3_all.csv")

#note: need a new (src, dst) column for dataframe, which is now based on 
#patent numbers
df3["srcdstpats"] = list(zip(df3["src"], df3["dst"]))

#filter for only active patents
active = df3[df3["year_src"] - df3["year_dst"] < 15]

#**************
#! NETWORK
#**************
years = range(1976, 2016)

G = setup_G(df3, "src", "dst")

tris, citations, triads = triads_and_cits(active, G, years)
shares = {year: x/y for year, x, y in zip(years, tris.values(), citations.values())}

active_disc = active[(active["technology_src"] == "discrete") & (active["technology_dst"] == "discrete")]
G = nx.create_empty_copy(G)
tris_disc, cits_disc, triads_disc = triads_and_cits(active_disc, G, years)
shares_disc = {year: x/y for year, x, y in zip(years, tris_disc.values(), citations.values())}

active_com = active[(active["technology_src"] == "complex") & (active["technology_dst"] == "complex")]
G = nx.create_empty_copy(G)
tris_com, cits_com, triads_com = triads_and_cits(active_com, G, years)
shares_com = {year: x/y for year, x, y in zip(years, tris_com.values(), citations.values())}