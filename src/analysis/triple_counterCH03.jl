using Pkg
using LightGraphs, GraphPlot, MetaGraphs
using CSV, DataFrames
using Plots

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
firms_path = joinpath(data_path, "firm_cluster_output/")
graph_path = joinpath(wd, "output/graphs_CH01/")

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

function make_df(raw_cites::DataFrame,
    raw_grants::DataFrame,
    raw_firms::DataFrame)

    edit_firms = new_ids(raw_firms, "firm_num")
    # Adding owner number
    owner_number = leftjoin(raw_grants, edit_firms, on = :patnum)

    # Getting the owners of the patents
    owner_source = leftjoin(raw_cites, edit_firms, on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, edit_firms, on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    dst_source = leftjoin(dst_source, raw_grants[:,["pubdate", "patnum"]], on = :src => :patnum)

    # Adding year from pubdate
    year_list = first.(string.(dst_source[!, "pubdate"]), 4)
    dst_source[!, "year"] = year_list

    # Narrowing it down
    df_out = dst_source[!, ["year", "firm_dst", "firm_src"]]

    return df_out
end

function drop_missings(df::DataFrame)
    df_out = dropmissing(df)
    return df_out
end

function rm_self_citations(df::DataFrame)
    # Removing those who cite themselves
    df_out = filter(x -> x["firm_src"] .!= x["firm_dst"], df)
    return df_out
end

function make_unique(df::DataFrame)
    # Only keeping unique combinations of firms
    df[!,"srcdst"] = tuple.(df[!,"firm_src"], df[!,"firm_dst"])

    return unique(df, "srcdst")
end

function unique_tuples(df::DataFrame)
    unique_pairs = unique!(tuple.(df[!, "firm_src"], df[!, "firm_dst"]))

    srcs = [unique_pairs[i][1] for i in range(1, stop=length(unique_pairs))]
    dsts = [unique_pairs[i][2] for i in range(1, stop=length(unique_pairs))]

    return srcs, dsts
end


function make_graph(df::DataFrame)
    # Makes the graph for further analysis

    # Only take unique values so that we are comparing thickets among firms not patents
    srcs, dsts = unique_tuples(df)

    m = get_max(srcs, dsts)
    G = DiGraph(m)

    for (i, el) in enumerate(srcs)
        add_edge!(G, srcs[i], dsts[i])
    end

    return G
end

function make_graph2(tuples::Vector{Tuple{Int64, Int64}})
    srcs = [tuples[i][1] for i in range(1, stop=length(tuples))]
    dsts = [tuples[i][2] for i in range(1, stop=length(tuples))]
    m = get_max(srcs, dsts)
    G = Graph(m)

    for (i, el) in enumerate(srcs)
        add_edge!(G, srcs[i], dsts[i])
    end

    return G
end

function get_max(src_numbers, dst_numbers)
    max_src = findmax(src_numbers)[1]
    max_dst = findmax(dst_numbers)[1]

    return max(max_src, max_dst)[1]
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

function tuple_to_vec(tpl::Vector{Tuple{Int64, Int64}})
    # Turns a tuple into a vector
    srcs = [tpl[i][1] for i in range(1, stop=length(tpl))]
    dsts = [tpl[i][2] for i in range(1, stop=length(tpl))]
    return srcs, dsts
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
    plot(xs, ratio, title=title)
    savefig(join([graph_path, name, ".png"]))
end

###############################################################################

cd(firms_path)
df_firm_grant = CSV.read("grant_firm.csv")
#matches patnum to firm_num

cd(data_path)
df_grants = CSV.read("grant_grant1990-2000.csv")
df_cite = CSV.read("grant_cite1990-2000.csv")


df1 = make_df(df_cite, df_grants, df_firm_grant)
df2 = drop_missings(df1)
df3 = rm_self_citations(df2)
df4 = make_unique(df3)

plot_ratios(df4, df4, "num: only unique edges, denom: only unique edges", "4")

a, b = count_trs(df4, df4)


# # Adapting Luci's data for my purposes
# df_luci = CSV.read("net_df.csv")
# df_luci[!,["owner_src", "owner_dst", "year"]]
# df_luci = rename(df_luci, "owner_src" => "firm_src")
# df_luci = rename(df_luci, "owner_dst" => "firm_dst")
# df_luci[!,"srcdst"] = tuple.(df_luci[!,"firm_src"], df_luci[!,"firm_dst"])
# df_luci[!, "year"] = string.(df_luci[!, "year"])
