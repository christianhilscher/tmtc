"""
This file contains the auxilary functions used for the triangle counting and weights.
"""

## Functions

"""
Takes a graph object as input and only returns those neighbors who cite both ways
"""
function makeundirected(graph::MetaDiGraph)


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
                push!(boths, Tuple(sort!([v, i])))
            end
        end
    end

    return unique!(boths)
end

insorted(item, collection) = !isempty(searchsorted(collection, item))

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
Own triangle count returning tuples
"""
function triangle_count_tuple(g::AbstractMetaGraph)
    ntri = Vector{Tuple{Int64, Int64, Int64}}(undef, nv(g))
    deg = degree(g)

    # list of tuples indicating each triangle
    out_list = Vector{Tuple{Int64, Int64, Int64}}()
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
                    push!(out_list, Tuple(sort([u, v, w])))
                end
            end
        end
    end
    return out_list
end


function sumweights(g::MetaGraph, j::Int64, k::Int64, l::Int64)

    out = sum([get_prop(g, Edge(j, k), :count),
                get_prop(g, Edge(j, l), :count),
                get_prop(g, Edge(k, l), :count)])
    return out
end

function add_instancecount!(graph::AbstractGraph, edge::Tuple{Int64, Int64})

    val = add_edge!(graph, edge)

    if val == true
        set_prop!(graph, Edge(edge), :count, 1)
    else
        tmp = get_prop(graph, edge[1], edge[2], :count)
        set_prop!(graph, Edge(edge), :count, tmp + 1)
    end
end

function get_weights(graph::MetaDiGraph, tuples::Vector{Tuple{Int64, Int64}})

    weights = Vector{Int64}(undef, length(tuples))

    for (ind, t) in enumerate(tuples)
        weights[ind] = get_prop(graph, t[1], t[2], :count) + get_prop(graph, t[2], t[1], :count)
    end
    return weights
end


function undirected_data(graph::AbstractGraph)

    T_undirected = makeundirected(graph)
    ws = get_weights(graph, T_undirected)

    return DataFrame(:srcdst => T_undirected, :count => ws)
end

function sumoftriangle(t::Tuple{Int64, Int64, Int64}, graph::MetaGraph)

    out = 0.0
    out = sum([get_prop(graph, t[1], t[2], :count),
                get_prop(graph, t[1], t[3], :count),
                get_prop(graph, t[2], t[3], :count)])
    return out
end

function get_triangleweighted(tuples::Vector{Tuple{Int64, Int64, Int64}}, graph::MetaGraph)
    cond = [i != (0, 0, 0) for i in tuples]
    tuples = tuples[cond]
    out = Vector{Int64}(undef, length(tuples))

    for (ind, tupl) in enumerate(tuples)
        out[ind] = sumoftriangle(tupl, graph)
    end
    return out
end
