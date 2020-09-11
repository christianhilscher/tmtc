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

function vertex_dict(df::DataFrameRow)
    dici = Dict()
    dici[:patnum] = df[:src]
    dici[:year] = df[:year_src]
    dici[:technology] = df[:technology_src]
    dici[:field_num] = df[:field_num_src]
    dici[:subcategory_id] = df[:subcategory_id_src]

    return dici
end

function edge_dict(df::DataFrameRow)
    dici = Dict()
    dici[:patnum] = (df[:src], df[:dst])
    dici[:year] = (df[:year_src], df[:year_dst])
    dici[:technology] = (df[:technology_src], df[:technology_dst])
    dici[:field_num] = (df[:field_num_src], df[:field_num_dst])
    dici[:subcategory_id] = (df[:subcategory_id_src], df[:subcategory_id_dst])

    return dici
end

function addinfo_vertex!(graph::MetaGraph, df::DataFrame)
    @progress for i in eachindex(df[!,:src])
        set_prop!(graph, df[i, :firm_src], Symbol(df[i, :src]), vertex_dict(df[i,:]))
    end
end

function addinfo_edge!(graph::MetaGraph, df::DataFrame)
    @progress for i in eachindex(df[!,:src])
        set_prop!(graph, Edge(df[i,:srcdst]), Symbol((df[i,:src], df[i, :dst])), edge_dict(df[i,:]))
    end
end

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

function makeundirected1(graph::MetaDiGraph)


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
            else
                rem_edge!(graph, i, v)
            end
        end
    end

    return boths
end


cd(data_path_tmp)

df3 = CSV.read("df3.csv")

df3[!, "srcdst"] = [(df3[i, :firm_src], df3[i, :firm_dst]) for i in eachindex(df3[!, :firm_src])]
df= df3

n_nodes = maximum([maximum(df[!,:firm_src]), maximum(df[!,:firm_dst])])

G1 = MetaDiGraph(n_nodes)
G2 = MetaGraph(n_nodes)

for el in df[!, "srcdst"]
    # add_instancecount!(G1, el)
    add_edge!(G1, el)
end

T_undirected = makeundirected(G1)
for el in T_undirected
    # add_instancecount!(G2, el)
    add_edge!(G2, el)
end

addinfo_vertex!(G2, df)
addinfo_edge!(G2, df)


cond = (() & (df[:technology_dst] .== "complex"))
cond = (df[!, :technology_src] .== "complex") .+ (df[!, :technology_dst] .== "complex") .== 2
convert(Bool, cond)

filter([:technology_src, :technology_dst] => (x, y) -> (x, y) == ("complex", "complex"), df)

df[!,:technology_src] .== df[!,:technology_dst]



v1 = 123486
v2 = 128209


abc = props(G2, v1, v2)

function eval_technology(dici::Dict)

    out_dict = Dict()
    out_dict[:coco] = 0.0
    out_dict[:didi] = 0.0
    out_dict[:dico] = 0.0
    out_dict[:codi] = 0.0

    for i in collect(values(dici))
        if i[:technology] == ("complex", "complex")
            out_dict[:coco] += 1
        elseif i == ("discrete", "complex")
            out_dict[:dico] += 1
        elseif i == ("discrete", "discrete")
            out_dict[:didi] += 1
        elseif i == ("complex", "discrete")
            out_dict[:codi] += 1
        end
    end
    return out_dict
end

@time eval_technology(abc)

for i in collect(values(abc))
    if i[:technology] == ("discrete", "discrete")
        println(i[:technology])
    end
end
