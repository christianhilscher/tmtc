using Pkg
using LightGraphs
using GraphPlot
using CSV
using DataFrames
using Traceur

df_grants = CSV.read("/Users/christianhilscher/Desktop/tmtc/data/grant_grant1990-2000.csv")
df_cite = CSV.read("/Users/christianhilscher/Desktop/tmtc/data/grant_cite1990-2000.csv")
df_ipc = CSV.read("/Users/christianhilscher/Desktop/tmtc/data/grant_ipc1990-2000.csv")


##############################################################################
function assign_owners(df_citations::DataFrame, df_owners::DataFrame, n::Int64)

    # Assigning the owners of the source
    owner_source = leftjoin(df_citations[1:n,:], df_owners[:,["owner", "patnum", "pubdate"]], on = :src => :patnum)
    owner_source = rename(owner_source, "owner" => "owner_src")

    # Assigning the owners of the destination
    dst_source = leftjoin(owner_source, df_owners[:,["owner", "patnum"]], on = :dst => :patnum)
    dst_source = rename(dst_source, "owner" => "owner_dst")

    # Adding year from pubdate
    year_list = first.(string.(dst_source[!, "pubdate"]), 4)
    dst_source[!, "year"] = year_list

    return dst_source
end

function drop_missings(df::DataFrame)
    out = dropmissing(df)
    return out
end

function assign_numbers(df::DataFrame)
    # Getting one integer for each firm
    # Need the integers to plot the graphs afterwards (I think)

    names = append!(string.(df[!, "owner_src"]), string.(df[!, "owner_dst"]))

    nums = DataFrame([unique(names), Array{Int64}(1:length(unique(names)))])

    df_with_numbers = make_numbers(df, nums)

    return df_with_numbers
end

function make_numbers(df::DataFrame, number_df::DataFrame)
    # First source
    df_joined = leftjoin(df, number_df, on = :owner_src => :x1)
    df_joined = rename(df_joined, "x2" => "owner_src_number")

    # Now destination
    df_joined = leftjoin(df_joined, number_df, on = :owner_dst => :x1)
    df_joined = rename(df_joined, "x2" => "owner_dst_number")

    # Delete those who cite themselves
    cond = isequal.(df_joined[!, "owner_src_number"], df_joined[!, "owner_dst_number"])
    df_out = df_joined[.!cond,:]

    return df_out
end

function unique_tuples(df::DataFrame)
    unique_pairs = unique!(tuple.(df[!, "owner_src_number"], df[!, "owner_dst_number"]))

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

##############################################################################

n = size(df_cite)[1]
const n_red = 1000000
joined1 = assign_owners(df_cite, df_grants, 1000000)
joined2 = drop_missings(joined1)
joined3 = assign_numbers(joined2)

ratios = count_trs(joined3, joined1)

ratios[1]./ratios[2]
