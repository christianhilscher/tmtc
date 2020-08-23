using Pkg
using LightGraphs, MetaGraphs, SimpleWeightedGraphs
using CSV, DataFrames
using PlotlyJS
using BenchmarkTools
using Random


wd = pwd()

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

###############################################################################
"""
Takes a graph object as input and only returns those neighbors who cite both ways
"""
function makeundirected(graph::MetaGraph)


    boths = Array{Tuple{Int64, Int64}}(undef, 0)
    # Loop over every vertice
    for v in vertices(graph)
        ins = Array{Int64}(undef)
        outs = Array{Int64}(undef)

        ins = inneighbors(graph, v)
        outs = outneighbors(graph, v)

        # Loop over all neighbors of vertice v to see whether the connection goes both ways
        for i in ins
            if in(i, outs)
                push!(boths, (v, i))
            end
        end
    end

    return boths
end

insorted(item, collection) = !isempty(searchsorted(collection, item))

"""
Own triangle count with function for how to handle weights
"""
function triangle_count(g::MetaGraph)
    ntri = zeros(length(vertices(g)))
    deg = degree(g)
    # create a degree-ordered directed graph where the original
    # undirected edges are directed from low-degree to high-degree
    adjlist = [Vector{Int64}() for _ in vertices(g)]
    @inbounds for u in vertices(g)
        for v in neighbors(g, u)
            # add edge u => v in pruned graph only if degv > degu
            # (or v > u for tie breaking)
            if deg[v] > deg[u] || (deg[v] == deg[u] && v > u)
                push!(adjlist[u], v)
            end
        end
    end
    @inbounds for u in vertices(g)
        adju = adjlist[u]
        lenu = length(adju)
        # chose u as pivot and check all pairs of its neighbors
        for i = 1:lenu
            v = adju[i]
            for j = i+1:lenu
                w = adju[j]
                # for every pair of edges u => v, u => w in the pruned graph
                # if an edge exists between v, w in the original graph we have found
                # a triangle. we check this by searching in the pruned graph instead
                # of the original graph to reduce search space
                wTov = (deg[v] > deg[w] || (deg[v] == deg[w] && v > w))
                if (wTov && insorted(v, adjlist[w])) ||
                        (!wTov && insorted(w, adjlist[v]))
                    ntri[u] += 1
                end
            end
        end
    end
    return ntri
end

"""
Own triangle count with function for how to handle weights
"""
function triangle_count_weights(g::MetaGraph)
    ntri = zeros(length(vertices(g)))
    deg = degree(g)
    # create a degree-ordered directed graph where the original
    # undirected edges are directed from low-degree to high-degree
    adjlist = [Vector{Int64}() for _ in vertices(g)]
    @inbounds for u in vertices(g)
        for v in neighbors(g, u)
            # add edge u => v in pruned graph only if degv > degu
            # (or v > u for tie breaking)
            if deg[v] > deg[u] || (deg[v] == deg[u] && v > u)
                push!(adjlist[u], v)
            end
        end
    end
    @inbounds for u in vertices(g)
        adju = adjlist[u]
        lenu = length(adju)
        # chose u as pivot and check all pairs of its neighbors
        for i = 1:lenu
            v = adju[i]
            for j = i+1:lenu
                w = adju[j]
                # for every pair of edges u => v, u => w in the pruned graph
                # if an edge exists between v, w in the original graph we have found
                # a triangle. we check this by searching in the pruned graph instead
                # of the original graph to reduce search space
                wTov = (deg[v] > deg[w] || (deg[v] == deg[w] && v > w))
                if (wTov && insorted(v, adjlist[w])) ||
                        (!wTov && insorted(w, adjlist[v]))
                    ntri[u] = sumweights(g, u, v, w)
                end
            end
        end
    end
    return ntri
end

"""
Own triangle count with function for how to handle weights
"""
function triangle_count_tuple(g::MetaGraph)
    ntri = Vector{Tuple{Int64, Int64, Int64}}(undef, nv(g))
    deg = degree(g)
    # create a degree-ordered directed graph where the original
    # undirected edges are directed from low-degree to high-degree
    adjlist = [Vector{Int64}() for _ in vertices(g)]
    @inbounds for u in vertices(g)
        for v in neighbors(g, u)
            # add edge u => v in pruned graph only if degv > degu
            # (or v > u for tie breaking)
            if deg[v] > deg[u] || (deg[v] == deg[u] && v > u)
                push!(adjlist[u], v)
            end
        end
    end
    @inbounds for u in vertices(g)
        adju = adjlist[u]
        lenu = length(adju)
        # chose u as pivot and check all pairs of its neighbors
        for i = 1:lenu
            v = adju[i]
            for j = i+1:lenu
                w = adju[j]
                # for every pair of edges u => v, u => w in the pruned graph
                # if an edge exists between v, w in the original graph we have found
                # a triangle. we check this by searching in the pruned graph instead
                # of the original graph to reduce search space
                wTov = (deg[v] > deg[w] || (deg[v] == deg[w] && v > w))
                if (wTov && insorted(v, adjlist[w])) ||
                        (!wTov && insorted(w, adjlist[v]))
                    ntri[u] = Tuple(sort([u, v, w]))
                end
            end
        end
    end
    return ntri
end


function sumweights(g::MetaGraph, j::Int64, k::Int64, l::Int64)

    out = sum([get_prop(g, Edge(j, k), :weight),
                get_prop(g, Edge(j, l), :weight),
                get_prop(g, Edge(k, l), :weight)])
    return out
end



"""
Take first differences to undo cumulation
"""
function uncumulate(arr::Vector{Int64})
    n = length(arr)
    out = zeros(n)

    for i in reverse(range(2,stop=n))
        out[i] = arr[i] - arr[i-1]
    end
    return out
end

## Loading finished data

cd(data_path_tmp)
df1 = CSV.read("df1.csv")
df2 = CSV.read("df2.csv")
df3 = CSV.read("df3.csv")
df4 = CSV.read("df4.csv")

## Playground

df = df3
df[!, "srcdst"] = [(df[i, :firm_src], df[i, :firm_dst]) for i in eachindex(df[!, :firm_src])]

n_nodes = maximum([maximum(df[!,:firm_src]), maximum(df[!,:firm_dst])])

G1 = MetaGraph(n_nodes)
G2 = MetaGraph(n_nodes)

for el in df[!, "srcdst"]
    add_instancecount!(G1, el)
end

T_undirected = makeundirected(G1)
for el in T_undirected
    add_instancecount!(G2, el)
end

# For now random weights to play around
rweights = rand(n_edges)

for (ind, element) in enumerate(edges(G2))
    set_prop!(G2, element, :weight, rweights[ind])
end

@time triangle_count_weights(G2)
@time triangle_count(G2)
abc = triangle_count_tuple(G2)

# Checkoing whether I have the same triangle count as it should be
triangle_count(G2).== triangles(G2)