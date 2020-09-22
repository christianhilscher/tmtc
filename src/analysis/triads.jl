using Pkg
using LightGraphs, MetaGraphs, SimpleWeightedGraphs
using CSV, DataFrames
using PlotlyJS
using BenchmarkTools, ProgressMeter, Profile
using Random

import Base.Threads.@spawn


wd = pwd()

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

###############################################################################
function identify_triads(g::SimpleDiGraph)
    ntri = 0

    deg = degree(g)
    outlist = [Vector{Int64}() for _ in vertices(g)]
    # list indicating all outneighbors of each vertex
    @inbounds for u in vertices(g)
        for v in outneighbors(g, u)
            push!(outlist[u], v)
        end
    end

    @inbounds for u in vertices(g)
        outu = outlist[u]
        lenu = length(outu)

        # looking through all outneighbors of vertex u
        for i = 1:lenu
            v = outu[i]

            # vertex v is an outneighbor of vertex u
            # checking outneighbors of vertex v
            # if outneighbor of vertex v is also an outneighbor of vertex v => triad
            for j in outlist[v]
                if in(j, outu)
                    ntri += 1
                end
            end
        end
    end
    return ntri
end

function id1(g::SimpleDiGraph)

    outlist = [Vector{Int64}() for _ in vertices(g)]
    # list indicating all outneighbors of each vertex
    @inbounds for u in vertices(g)
        for v in outneighbors(g, u)
            push!(outlist[u], v)
        end
    end
    triads = make_list(g, outlist)
    return triads
end

function make_list(g::SimpleDiGraph, neighborlist::Vector{Array{Int64, 1}})

    int_len = convert(Int, round(nv(g)/2))

    firsthalf = @spawn id2(neighborlist, 1:int_len)
    secondhalf = id2(neighborlist, int_len+1:nv(g))

    wait(firsthalf)

    res = fetch(firsthalf) + secondhalf
    return res
end

function id2(neighborlist, interv)
    ntri = 0
    for u = interv
        outu = neighborlist[u]
        lenu = length(outu)

        # looking through all outneighbors of vertex u
        for i = 1:lenu
            v = outu[i]

            # vertex v is an outneighbor of vertex u
            # checking outneighbors of vertex v
            # if outneighbor of vertex v is also an outneighbor of vertex v => triad
            for j in neighborlist[v]
                if in(j, outu)
                    ntri += 1
                end
            end
        end
    end
    return ntri
end


function filter_technology(df::DataFrame, tech::String)

    cond = df[!,:technology_src] .== df[!,:technology_dst] .== tech
    return df[cond,:]
end

function count_triangles(df::DataFrame)

    # Number of nodes is at most the maxmimum of src or dst
    n_nodes = maximum([maximum(df[!,:src]), maximum(df[!,:dst])])

    G_directed = SimpleDiGraph(n_nodes)

    years = sort(unique(df[!, :year_src]))
    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    # Counting each year separately
    for (ind, year) in enumerate(years)
        rel = view(df, df[!, :year_src].==year, :srcdst)
        for el in rel
            # add_instancecount!(G1, el)
            add_edge!(G_directed, el)
        end
        # Identifying triads and # of citations
        trs[ind] = identify_triads(G_directed)
        cts[ind] = length(rel)
    end

    # Since the triangles add up over the years also use the cumulative sum for citations
    return trs, cumsum(cts)
end
## Real data
cd(data_path_tmp)
df3 = CSV.read("df3.csv")
df3[!, :srcdst] = [(df3[i, :src], df3[i, :dst]) for i in eachindex(df3[!, :firm_src])]
df = df3[df3[!,:year_src] - df3[!,:year_dst] .< 15,:]


## First try w/ function

function triads_by_technology(dataf::DataFrame)

    df_complex = filter_technology(df, "complex")
    df_discrete = filter_technology(df, "discrete")

    firsthalf = @spawn count_triangles(df_discrete)
    complexx, complexy = count_triangles(df_complex)

    wait(firsthalf)

    discretex, discretey = fetch(firsthalf)

    return discretex, complexx
end

function triads_by_technology1(dataf::DataFrame)

    df_complex = filter_technology(df, "complex")
    df_discrete = filter_technology(df, "discrete")

    discretex, discretey = count_triangles(df_discrete)
    complexx, complexy = count_triangles(df_complex)

    return discretex, complexx
end

@time a, b = triads_by_technology(df)
@time c, d = triads_by_technology1(df)

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
