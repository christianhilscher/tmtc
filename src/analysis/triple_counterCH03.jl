using Pkg
using LightGraphs
using GraphPlot
using CSV
using DataFrames
using Traceur
using Plots

wd = "/Users/christianhilscher/Desktop/tmtc/"
data_path = joinpath(wd, "data/")
firms_path = joinpath(data_path, "firm_cluster_output/")

###############################################################################
function make_df(raw_cites::DataFrame,
    raw_grants::DataFrame,
    raw_firms::DataFrame)

    # Adding owner number
    owner_number = leftjoin(raw_grants, raw_firms, on = :patnum)

    # Getting the owners of the patents
    owner_source = leftjoin(raw_cites, raw_firms, on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, raw_firms, on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    dst_source = leftjoin(dst_source, raw_grants[:,["pubdate", "patnum"]], on = :src => :patnum)

    # Adding year from pubdate
    year_list = first.(string.(dst_source[!, "pubdate"]), 4)
    dst_source[!, "year"] = year_list

    # Narrowing it down
    narrow_df = dst_source[!, ["year", "firm_dst", "firm_src"]]

    # Dropping missings
    df_kept = dropmissing(narrow_df)
    # Removing those who cite themselves
    df_out = filter(x -> x["firm_src"] .!= x["firm_dst"], df_kept)

    return df_out
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
###############################################################################

cd(firms_path)
df_firm_grant = CSV.read("grant_firm.csv")
#matches patnum to firm_num

cd(data_path)
df_grants = CSV.read("grant_grant1990-2000.csv")
df_cite = CSV.read("grant_cite1990-2000.csv")


df1 = make_df(df_cite, df_grants, df_firm_grant)
df1[!,"srcdst"] = tuple.(df1[!,"firm_src"], df1[!,"firm_dst"])

df2 = unique(df1, "srcdst")

ratios = count_trs(df2, df2)

ratios
ratios[1]./ratios[2]

plot(1990:2000, ratios[1]./ratios[2])





df_luci = CSV.read("net_df.csv")
df_luci[!,["owner_src", "owner_dst", "year"]]
df_luci = rename(df_luci, "owner_src" => "firm_src")
df_luci = rename(df_luci, "owner_dst" => "firm_dst")


n_directed = size(df2, 1)
G_directed = DiGraph(n_directed)

for year in 1990:2000
    df_rel = df2[df2[!,"year"] .== string(year), :]
    add_to_graph(G_directed, df_rel[!,"firm_src"], df_rel[!,"firm_dst"])
end


n_undirected = size(make_undirected(G_directed), 1)
G_undirected = Graph(n_undirected)
G_clean = DiGraph(n_directed)

years = unique(df2[!, "year"])
trs = Array{Int64}(undef, length(years))
cts = Array{Int64}(undef, length(years))

for (ind, year) in enumerate(years)
    df_rel = df2[df2[!,"year"] .== string(year), :]
    df_rel_cites = df1[df1[!,"year"] .== string(year), :]
    add_to_graph(G_clean, df_rel[!,"firm_src"], df_rel[!,"firm_dst"])

    T_vec = make_undirected(G_clean)
    vec1, vec2 = tuple_to_vec(T_vec)
    for (i, el) in enumerate(vec1)
        add_edge!(G_undirected, vec1[i], vec2[i])
    end

    tmp = triangles(G_undirected)
    trs[ind] = sum(tmp)/3
    cts[ind] = size(df_rel_cites, 1)
end

cumsum(trs)

cumsum(trs)./cumsum(cts)
trs./cts
plot(years, cumsum(trs)./cumsum(cts))

(sum(triangles(G_undirected))/3)/size(df1, 1)
