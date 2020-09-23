using Pkg
using LightGraphs, MetaGraphs, SimpleWeightedGraphs
using CSV, DataFrames
using PlotlyJS
using BenchmarkTools, ProgressMeter, Profile
using Random, GraphPlot


wd = pwd()

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

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


function count_triangles(df::DataFrame)

    # Number of nodes is at most the maxmimum of firm_src or firm_dst
    n_nodes = maximum([maximum(df[!,"firm_src"]), maximum(df[!,"firm_dst"])])

    G_directed = MetaDiGraph(n_nodes)
    G_undirected = MetaGraph(n_nodes)

    years = sort(unique(df[!, :year_src]))
    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    # Counting each year separately
    for (ind, year) in enumerate(years)

        df_rel = df[df[!,:year_src] .== year, :]
        for el in df_rel[!, :srcdst]
            # add_instancecount!(G1, el)
            add_edge!(G_directed, el)
        end

        # Keeping only those where the connection goes both ways
        T_vec = makeundirected(G_directed)
        for (i, el) in enumerate(T_vec)
            add_edge!(G_undirected, T_vec[i])
        end

        # Counting triangles in that graph only containing both directions
        tmp = triangles(G_undirected)
        trs[ind] = sum(tmp)/3
        cts[ind] = length(unique(df_rel[!, :srcdst]))
    end

    # Since the triangles add up over the years also use the cumulative sum for citations
    return trs, cumsum(cts)
end

function filter_technology(df::DataFrame, tech::String)

    cond = df[!,:technology_src] .== df[!,:technology_dst] .== tech
    return df[cond,:]
end

## Data
cd(data_path_tmp)

df3 = CSV.read("df3.csv")

df3[!, "srcdst"] = [(df3[i, :firm_src], df3[i, :firm_dst]) for i in eachindex(df3[!, :firm_src])]
df = df3[df3[!,:year_src] - df3[!,:year_dst] .< 15,:]


df_complex = filter_technology(df, "complex")
df_discrete = filter_technology(df, "discrete")

discretex, discretey = count_triangles(df_discrete)
complexx, complexy = count_triangles(df_complex)
totalx, totaly = count_triangles(df)

## Plotting

function trs_over_cites(df_d::DataFrame, df_c::DataFrame, df_t::DataFrame)

    y1 = df_d[!,:trs]./df_t[!,:edges]
    y2 = df_c[!,:trs]./df_t[!,:edges]
    y3 = df_t[!,:trs]./df_t[!,:edges]

    trace1 = scatter(df_d, x = :year, y = y1, mode="lines", name="discrete triples")

    trace2 = scatter(df_c, x = :year, y = y2, mode="lines", name="complex triples")

    trace3 = scatter(df_t, x = :year, y = y3, mode="lines", name="total triples")

    layout = Layout(;title="Triples relative to edges in respective network")
    data = [trace1, trace2, trace3]
    plot(data, layout)
end


df_plot_discrete = DataFrame(:year => sort(unique(df_discrete[!,:year_src])), :trs => discretex, :edges => discretey)

df_plot_complex = DataFrame(:year => sort(unique(df_complex[!,:year_src])), :trs => complexx, :edges => complexy)

df_plot_total = DataFrame(:year => sort(unique(df[!,:year_src])), :trs => totalx, :edges => totaly)

trs_over_cites(df_plot_discrete, df_plot_complex, df_plot_total)

println(df_plot_total)
