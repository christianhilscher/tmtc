using Pkg
using LightGraphs, GraphPlot, MetaGraphs
using CSV, DataFrames
using Plots

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

###############################################################################
function new_ids(df_firm::DataFrame, var::String)

    df_firm = rename(df_firm, var => "tobechanged")
    df_new = df_firm[!, ["tobechanged"]]
    tmp_df = unique(df_new, "tobechanged")
    tmp_df[!, "firm_id"] = 1:size(tmp_df, 1)

    df_new = leftjoin(df_firm, tmp_df, on = :tobechanged)

    df_new = select(df_new, Not(:tobechanged))
    rename!(df_new, "firm_id" => var)

    return df_new
end

function make_undirected(graph::SimpleDiGraph)

    boths = Array{Tuple{Int64, Int64}}(undef, 0)
    for v in vertices(graph)
        ins = Array{Int64}(undef)
        outs = Array{Int64}(undef)

        ins = inneighbors(graph, v)
        outs = outneighbors(graph, v)

        for i in ins
            if in(i, outs)
                push!(boths, (v, i))
            end
        end
    end

    return boths
end

function add_to_graph(graph::SimpleDiGraph, srcs, dsts)

    for (i, el) in enumerate(srcs)
        add_edge!(graph, srcs[i], dsts[i])
    end
end

function count_trs(df::DataFrame, df_citations::DataFrame)

    n_directed = size(df, 1)
    G_directed = DiGraph(n_directed)
    # Filling first graph and make it undirected to get size of undirected one
    add_to_graph(G_directed, df[!,"firm_src"], df[!,"firm_dst"])


    n_undirected = size(make_undirected(G_directed), 1)
    G_undirected = Graph(n_undirected)
    G_clean = DiGraph(n_directed)

    years = sort(unique(df[!, "year"]))
    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    for (ind, year) in enumerate(years)

        df_rel = df[df[!,"year"] .== string(year), :]
        df_rel_cites = df_citations[df_citations[!,"year"] .== string(year), :]
        add_to_graph(G_clean, df_rel[!,"firm_src"], df_rel[!,"firm_dst"])


        T_vec = make_undirected(G_clean)
        for (i, el) in enumerate(T_vec)
            add_edge!(G_undirected, T_vec[i])
        end

        tmp = triangles(G_undirected)
        trs[ind] = sum(tmp)/3
        cts[ind] = size(df_rel_cites, 1)
    end

    return trs, cumsum(cts)
end

function plot_ratios(df::DataFrame,
    df_cites::DataFrame,
    title::String,
    name::String)

    xs = sort(unique(df[!,"year"]))
    triangles, cites = count_trs(df, df_cites)

    ratio = triangles./cites
    plot(xs, ratio, title=title, label = "ratio")
    savefig(join([graph_path, name, ".png"]))
end

###############################################################################

cd(data_path)

df1 = CSV.read("df1.csv")
df2 = CSV.read("df2.csv")
df3 = CSV.read("df3.csv")
df4 = CSV.read("df4.csv")
