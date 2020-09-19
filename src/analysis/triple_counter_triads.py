import numpy as np 
import pandas as pd 
import networkx as nx 
import os 
import itertools 

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)
#*now: new apporach to count triangles, namely DeGrazia et al. (2020) method

#*read in training data  
df3 = pd.read_csv("data/df3 3.csv")
#note: need a new (src, dst) column for dataframe, which is now based on 
#patent numbers
df3["srcdstpats"] = list(zip(df3["src"], df3["dst"]))
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

G = setup_G(df3, "src", "dst")
G = setup_G_edges(df3, G, edgecol = "srcdstpats")

def triads(G, nodes = None):
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
            #same for succs(k) and preds(j)
            preds_inter = preds_j.intersection(succs_noj)
            #now, that we have the intersections, combine them to 1 set 
            union = succs_inter.union(preds_inter)
            
            for x in union: 
                triads.append((k, j, x))
    return(triads)
