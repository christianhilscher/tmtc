import numpy as np 
import pandas as pd 
import networkx as nx 

#set up directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
wd_ch = "add me"
os.chdir(wd_lc)

#read in all data
#citations
cites = pd.read_csv("src/get_data/data/tables/grant_cite.csv")
#main file 
main = pd.read_csv("src/get_data/data/tables/grant_grant.csv")
#ipc (what is this?)
ipc = pd.read_csv("src/get_data/data/tables/grant_ipc.csv")

#! Goal 
#* filter mutual connections between two firms 
#* check whether they are overlapping 

#!Prepare data 
#we don't need the patent number but its holder 
#thus, merge cites with main - use a reduced form of the latter for better oversight (for now)
main_red = main[['patnum', 'owner', 'pubdate']]
#merge reduced main with the citations to get owner names of src 
merged = cites.merge(main_red, left_on = 'src', right_on = 'patnum', how = 'inner')
merged = merged.rename(columns = {'owner': 'owner_src'})
merged = merged.drop(['patnum', 'pubdate'], axis = 1)
#merge the new df with main AGAIN, but this time based on dst to get firm 
#names of dst owners
merged_2 = merged.merge(main_red, left_on = 'dst', right_on = 'patnum', how = 'inner')
merged_2 = merged_2.rename(columns = {'owner': 'owner_dst'})
#drop all rows which have no dst owners since they are of no use 
matched = merged_2.dropna(how = 'any').drop('patnum', axis = 1)
#turn publication date into year only 
def get_first(number, first = 4): 
    return(int(str(number)[:4]))
matched['pubdate'] = matched['pubdate'].apply(get_first, args = [4])
#drop everything where owner_src == owner_dst
matched = matched[matched['owner_src'] != matched['owner_dst']]
#we can also drop all observations in where owner_dst is not in 
#owner_src, since in such a case a mutual directed edge is not possible 
#but first get total number of references in 2010
tot_ref = len(matched[matched['pubdate'] == 2010])
matched = matched[matched['owner_dst'].isin(matched['owner_src'])].reset_index(drop = True)
'''
thought !!
need to/can reduce the dataset further: 
if 1 src cites several dst from same owner_dst then 1 entry is enough 
'''
#!Network analysis 
#create a network of df using NetworkX lib
#for testing purposes only use data from 2010 
'''
#!Try 1
matched_2010 = matched[matched['pubdate'] == 2010]

G = nx.from_pandas_edgelist(matched_2010, source = 'owner_src', target = 'owner_dst', create_using = nx.DiGraph())
mat = nx.to_numpy_matrix(G)

#for each node, get successors and predeccors, add the ones that are in both 
#to "both_dir" and then create a dictionary with key = node and values = both_dir
node_dict = {}
for node in list(G.nodes):
    succec = list(G.successors(node))
    predec = list(G.predecessors(node))
    both_dir = []
    for x in succec: 
        if x in predec: 
            both_dir.append(x)
        node_dict[x] = both_dir

#create a new graph, now only containing the ones that are connected with predecessor and successor
new_graph = nx.from_dict_of_lists(node_dict, create_using = nx.Graph())
#now get the triangles, which in turn MUST be with mutual direction edges 
#following from procedure above 
tri = nx.triangles(new_graph)
tri_arr = np.array(list(tri.values()))
#docs say that each triangle is counted 3 times when applying it to the whole graph 
tri_arr = np.sum(tri_arr)/3

patent_dens = tri_arr/tot_ref #0.2352 ->way too large, this isn't correct yet
'''

#!Try 2
thicket_dict = {}
for year in [2010, 2011, 2012, 2013, 2014]:
    matched_year = matched[matched['pubdate'] == year]
    G = nx.DiGraph()
    #add nodes 
    owners_src = matched_year['owner_src'].tolist() 
    owners_dst = matched_year['owner_dst'].tolist()
    nodes = owners_src + owners_dst
    #remove duplicates of firms 
    nodes = list(dict.fromkeys(nodes))
    G.add_nodes_from(nodes)
    edges = list(zip(matched_year['owner_src'], matched_year['owner_dst']))
    edges = list(set([i for i in edges]))
    G.add_edges_from(edges)

    node_dict = {}
    for x in list(G.nodes):
        neigh = list(G.neighbors(x))
        predec = list(G.predecessors(x))
        both_dir = []
        for y in neigh: 
            if y in predec: 
                both_dir.append(y)
        node_dict[x] = both_dir

    for k, v in list(node_dict.items()): 
        if v == []: 
            del node_dict[k]

    G_new = nx.Graph(node_dict)
    tris = list(nx.triangles(G_new).values())
    tris_arr = np.array(tris)
    tris_sum = np.sum(tris_arr)/3
    tot_ref = len(matched[matched['pubdate'] == year])
    thicket_dict[str(year)] = tris_sum/tot_ref