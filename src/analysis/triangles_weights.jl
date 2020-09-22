using Pkg
using LightGraphs, MetaGraphs, SimpleWeightedGraphs
using CSV, DataFrames
using PlotlyJS
using BenchmarkTools, ProgressMeter, Profile
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

function triangles_from_df(dataf::DataFrame)

    n_nodes = maximum([maximum(dataf[!,:firm_src]), maximum(dataf[!,:firm_dst])])

    # Initialize Graphs
    G_directed = MetaDiGraph(n_nodes)
    G_undirected = MetaGraph(n_nodes)

    years = sort(unique(df[!, :year_src]))
    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    # Counting each year separately
    for (ind, year) in enumerate(years)

        df_rel = dataf[dataf[!,:year_src] .== year, :]

        for el in df_rel[!, :srcdst]
            add_instancecount!(G_directed, el)
        end

        # Getting the tuple and the number of connections between them
        df = undirected_data(G_directed)

        for i = 1:size(df, 1)
            add_edge!(G_undirected, df[i, :srcdst])
            set_prop!(G_undirected, df[i, :srcdst][1], df[i, :srcdst][2], :count, df[i, :count])
        end

        # Getting the tuple (X, Y, Z) which form a triangle
        all_tuples = triangle_count_tuple(G_undirected)
        # Getting the corresponding weights
        out_list = get_triangleweighted(all_tuples, G_undirected)

        # Summing over the weights for total
        trs[ind] = sum(out_list)
        cts[ind] = size(df_rel, 1)
    end
    return trs, cumsum(cts)
end

function filter_technology(df::DataFrame, tech::String)

    cond = df[!,:technology_src] .== df[!,:technology_dst] .== tech
    return df[cond,:]
end
## Loading finished data

cd(data_path_tmp)
df3 = CSV.read("df3.csv")


## Playground


df3[!, "srcdst"] = [(df3[i, :firm_src], df3[i, :firm_dst]) for i in eachindex(df3[!, :firm_src])]
df = df3[df3[!,:year_src] - df3[!,:year_dst] .< 15,:]

df_complex = filter_technology(df, "complex")
df_discrete = filter_technology(df, "discrete")

discretex, discretey = triangles_from_df(df_discrete)
complexx, complexy = triangles_from_df(df_complex)
totalx, totaly = triangles_from_df(df)

## Plotting

function trs_over_cites(df_d::DataFrame, df_c::DataFrame, df_t::DataFrame)

    y1 = df_d[!,:trs]./df_t[!,:edges]
    y2 = df_c[!,:trs]./df_t[!,:edges]
    y3 = df_t[!,:trs]./df_t[!,:edges]

    trace1 = scatter(df_d, x = :year, y = y1, mode="lines", name="discrete triples")

    trace2 = scatter(df_c, x = :year, y = y2, mode="lines", name="complex triples")

    trace3 = scatter(df_t, x = :year, y = y3, mode="lines", name="total triples")

    layout = Layout(;title="Weighted triangles relative to total citations")
    data = [trace1, trace2, trace3]
    plot(data, layout)
end

df_plot_discrete = DataFrame(:year => sort(unique(df_discrete[!,:year_src])), :trs => discretex, :edges => discretey)

df_plot_complex = DataFrame(:year => sort(unique(df_complex[!,:year_src])), :trs => complexx, :edges => complexy)

df_plot_total = DataFrame(:year => sort(unique(df[!,:year_src])), :trs => totalx, :edges => totaly)

trs_over_cites(df_plot_discrete, df_plot_complex, df_plot_total)
