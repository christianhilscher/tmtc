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
"""
Identifying triads according to deGrazia et al. (2020)
"""
function identify_triads(g::SimpleDiGraph)

    outlist = [Vector{Int64}() for _ in vertices(g)]
    # list indicating all outneighbors of each vertex
    @inbounds for u in vertices(g)
        for v in outneighbors(g, u)
            push!(outlist[u], v)
        end
    end

    triads = triadcount(outlist, 1:nv(g))
    return triads
end

"""
Returning tuples of triads
"""
function identify_triads_tuples(g::SimpleDiGraph)

    outlist = [Vector{Int64}() for _ in vertices(g)]
    # list indicating all outneighbors of each vertex
    @inbounds for u in vertices(g)
        for v in outneighbors(g, u)
            push!(outlist[u], v)
        end
    end

    triads = triadtuples(outlist, 1:nv(g))
    return triads
end

"""
Same function as before just running on two processors
No idea yet whether this is actually faster because of overhead
"""
function identify_triads_multicore(g::SimpleDiGraph)

    outlist = [Vector{Int64}() for _ in vertices(g)]
    # list indicating all outneighbors of each vertex
    @inbounds for u in vertices(g)
        for v in outneighbors(g, u)
            push!(outlist[u], v)
        end
    end

    # next function takes over second part
    triads = splitwork(g, outlist)
    return triads
end

"""
Splitting the work over two threads
"""
function splitwork(g::SimpleDiGraph, neighborlist::Vector{Array{Int64, 1}})

    # For now split by length of neighborlist; probably some sort of weight
    # would be better since a lot of the elements are 0
    int_len = convert(Int, round(nv(g)/2))

    firsthalf = @spawn triadcount(neighborlist, 1:int_len)
    secondhalf = triadcount(neighborlist, int_len+1:nv(g))

    # Only continuing after first half is done
    wait(firsthalf)

    # since both return the number of triads, summing them works
    res = fetch(firsthalf) + secondhalf
    return res
end

"""
Counting triads given a neighborlist and an intervall of vertices
"""
function triadcount(neighborlist::Vector{Array{Int64, 1}}, interv::UnitRange{Int64})
    ntri = 0

    # u is a UnitRange here so iteration works
    @inbounds for u = interv
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

"""
Returning all the tuples of a given triangle
"""
function triadtuples(neighborlist::Vector{Array{Int64, 1}}, interv::UnitRange{Int64})
    ntri = Vector{Tuple{Int64, Int64, Int64}}(undef, length(interv))

    # u is a UnitRange here so iteration works
    @inbounds for u = interv
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
                    push!(ntri, tuple(u, i, j))
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

"""
Wrapper for most often used function

    * Getting the triads/triangles for each year separately
    * Since the edges are added to graph on a yearly basis, the triad count is already cumulative
"""
function count_triangles(df::DataFrame)

    # Number of nodes is at most the maxmimum of src or dst
    # n_nodes = maximum([maximum(df[!,:src]), maximum(df[!,:dst])])

    # Initializig graph and arrays
    G_directed = SimpleDiGraph()
    years = sort!(unique(df[!, :year_src]))
    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    # Counting each year separately
    for (ind, year) in enumerate(years)
        # Using a view here for smaller memory allocation
        rel = view(df, df[!, :year_src].==year, :srcdst)

        for el in rel
            add_edge!(G_directed, el)
        end

        # Identifying triads and # of citations
        trs[ind] = identify_triads_multicore(G_directed)
        cts[ind] = length(rel)
    end

    # Since the triangles add up over the years also use the cumulative sum for citations
    return trs, cumsum(cts)
end

## Real data
cd(data_path_tmp)

df3 = CSV.read("df3_CH.csv")
df3[!, :srcdst] = [(df3[i, :src], df3[i, :dst]) for i in eachindex(df3[!, :firm_src])]
df = df3[df3[!,:year_src] - df3[!,:year_dst] .< 15,:]

## Calculating

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
