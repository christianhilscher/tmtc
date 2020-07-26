using Pkg
using LightGraphs
using GraphPlot
using CSV
using DataFrames

df_grants = CSV.read("/Users/christianhilscher/Desktop/tmtc/data/grant_grant.csv")
df_cite = CSV.read("/Users/christianhilscher/Desktop/tmtc/data/grant_cite.csv")
df_ipc = CSV.read("/Users/christianhilscher/Desktop/tmtc/data/grant_ipc.csv")


##############################################################################
function assign_owners(df_citations::DataFrame, df_owners::DataFrame, n::Int64)

    # Assigning the owners of the source
    owner_source = leftjoin(df_citations[1:n,:], df_owners[:,["owner", "patnum"]], on = :src => :patnum)
    owner_source = rename(owner_source, "owner" => "owner_src")

    # Assigning the owners of the destination
    dst_source = leftjoin(owner_source, df_owners[:,["owner", "patnum"]], on = :dst => :patnum)
    dst_source = rename(dst_source, "owner" => "owner_dst")

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
    df_out = leftjoin(df, number_df, on = :owner_src => :x1)
    df_out = rename(df_out, "x2" => "owner_src_number")

    # Now destination
    df_out = leftjoin(df_out, number_df, on = :owner_dst => :x1)
    df_out = rename(df_out, "x2" => "owner_dst_number")

    return df_out
end

function make_graph(df::DataFrame)
    # Makes the graph for further analysis
    srcs = convert(Array{Int64}, df[!, "owner_src_number"])
    dsts = convert(Array{Int64}, df[!, "owner_dst_number"])

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


const n = size(df_cite)[1]
joined1 = assign_owners(df_cite, df_grants, n)
joined2 = drop_missings(joined1)
joined3 = assign_numbers(joined2)

G = make_graph(joined3)
