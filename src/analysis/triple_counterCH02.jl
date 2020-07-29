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
    owner_source = leftjoin(raw_cites, owner_number[:,["firm_num", "patnum", "pubdate"]], on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, owner_number[:,["firm_num", "patnum"]], on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    # Adding year from pubdate
    year_list = first.(string.(dst_source[!, "pubdate"]), 4)
    dst_source[!, "year"] = year_list

    out_df = dst_source[!, ["year", "firm_dst", "firm_src"]]
    return out_df
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

function count_trs(df::DataFrame, df_cites::DataFrame)

    years = unique(df[!, "year"])

    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    for (ind, y) in enumerate(years)
        # Taking years one-by-one
        df_relevant = df[df[!, "year"] .== y, :]
        df_relevant_cites = df_cites[df_cites[!, "year"] .== y, :]

        G = make_graph(df_relevant)
        T_vec = make_undirected(G)
        G2 = make_graph2(T_vec)

        # Every triangle is counted 3 times
        tmp = triangles(G2)
        trs[ind] = sum(tmp)/3
        cts[ind] = size(df_relevant_cites)[1]
    end


    sum_trs = cumsum(trs)
    sum_cts = cumsum(cts)

    return sum_trs, sum_cts
end
###############################################################################

cd(firms_path)
df_firm_grant = CSV.read("grant_firm.csv")
#matches patnum to firm_num

cd(data_path)
df_grants = CSV.read("grant_grant1990-2000.csv")
df_cite = CSV.read("grant_cite1990-2000.csv")


df1 = make_df(df_cite, df_grants, df_firm_grant)


size(dropmissing(df1))[1]/size(df1)[1]
df2 = dropmissing(df2)

ratios = count_trs(df2, df1)
ratios[1]./ratios[2]

plot(1990:2000, ratios[1]./ratios[2])
