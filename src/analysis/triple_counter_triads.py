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
        tris = get_triads(G_di)
        #add everything to dictionaries 
        tri_dict[i] = tris 
        cit_dict[i] = tot_cit
        print(i)
    return(tri_dict, cit_dict)

#**************
#! DATA
#**************
df3 = pd.read_csv("data/df3 3.csv")
#note: need a new (src, dst) column for dataframe, which is now based on 
#patent numbers
df3["srcdstpats"] = list(zip(df3["src"], df3["dst"]))
#filter for only active patents
active = df3[df3["year_src"] - df3["year_dst"] < 15]

#**************
#! NETWORK
#**************
years = range(1976, 2001)
G = setup_G(df3, "src", "dst")

triads, citations = triads_and_cits(active, G, years)