using Pkg
using LightGraphs, MetaGraphs
using CSV, DataFrames
using PlotlyJS

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
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

function make_df(raw_cites::DataFrame,
    raw_grants::DataFrame,
    raw_firms::DataFrame)
    """
    Takes the raw data files and merges them into somthing useable
    """

    edit_firms = new_ids(raw_firms, "firm_num")

    # Getting the owners of the patents
    owner_source = leftjoin(raw_cites, edit_firms, on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, edit_firms, on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    dst_source = leftjoin(dst_source, raw_grants[:,["pubdate", "patnum", "ipc", "ipcver"]], on = :src => :patnum)

    # Adding year from pubdate
    year_list = first.(string.(dst_source[!, "pubdate"]), 4)
    dst_source[!, "year"] = year_list

    # Narrowing it down
    df_out = dst_source[!, ["year", "firm_dst", "firm_src", "ipc", "ipcver"]]

    return df_out
end

function add_ipc(df::DataFrame, df_ipc::DataFrame)
    """
    Adding the ipc classification to the main dataframe
    """

    df_ipc = unique(df_ipc, "ipc_code")

    df = dropmissing(df, "ipc")
    df[!, "ipc_code"] = first.(df[!, "ipc"], 4)
    df_ipc = leftjoin(df, unique(df_ipc, "ipc_code"), on = :ipc_code)

    return df_ipc
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

function make_undirected(graph::SimpleDiGraph)
    """
    Takes a graph object as input and only returns those neighbors who cite both ways
    """

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

function add_to_graph(graph::SimpleDiGraph, srcs, dsts)

    for (i, el) in enumerate(srcs)
        add_edge!(graph, srcs[i], dsts[i])
    end
end

function count_trs(df::DataFrame, df_citations::DataFrame)

    # Number of nodes is at most the maxmimum of firm_src or firm_dst
    n_nodes = maximum([maximum(df[!,"firm_src"]), maximum(df[!,"firm_dst"])])

    G_directed = DiGraph(n_nodes)
    G_undirected = Graph(n_nodes)

    years = sort(unique(df_citations[!, "year"]))
    trs = Array{Int64}(undef, length(years))
    cts = Array{Int64}(undef, length(years))

    # Counting each year separately
    for (ind, year) in enumerate(years)

        df_rel = df[df[!,"year"] .== year, :]
        df_rel_cites = df_citations[df_citations[!,"year"] .== year, :]
        add_to_graph(G_directed, df_rel[!,"firm_src"], df_rel[!,"firm_dst"])

        # Keeping only those where the connection goes both ways
        T_vec = make_undirected(G_directed)
        for (i, el) in enumerate(T_vec)
            add_edge!(G_undirected, T_vec[i])
        end

        # Counting triangles in that graph only containing both directions
        tmp = triangles(G_undirected)
        trs[ind] = sum(tmp)/3
        cts[ind] = size(df_rel_cites, 1)
    end

    # Since the triangles add up over the years also use the cumulative sum for citations
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

function linescatter1(df::DataFrame)
    trace1 = scatter(df, x = :year_list, y = :ratio_d, mode="lines", name="discrete industries")

    trace2 = scatter(df, x = :year_list, y = :ratio_c, mode="lines", name="complex industries")

    plot([trace1, trace2])
end

function count_by_fields(df::DataFrame, df_citations::DataFrame, variable::String)

    """
    Counting triangles but differentiating by some variable first.
    """
    categories = sort(unique(df[!, variable]))

    xs = sort(unique(df_citations[!,"year"]))
    df_hold = DataFrame(year = xs)

    for (ind, cat) in enumerate(categories)
        println(cat)
        # Making names for dataframe
        name1 = join(["trs_", cat])
        name2 = join(["cites_", cat])

        # Conditional counting
        x1, x2 = count_trs(df[df[!,variable].==cat,:], df_citations)
        df_hold[!, name1] = x1
        df_hold[!, name2] = x2

    end
    return df_hold
end

function un_cumulate(arr::Vector{Int64})
    n = length(arr)
    out = zeros(n)

    for i in reverse(range(2,stop=n))
        out[i] = arr[i] - arr[i-1]
    end
    return out
end
###############################################################################
## Reading in and making data

# cd(data_path_full)
# df_firm_grant = CSV.read("grant_firm.csv")
# df_grants = CSV.read("grant_grant.csv")
# df_cite = CSV.read("grant_cite.csv")
#
# df_cite = dropmissing(df_cite)
# sum(df_cite[!, "src"] .> df_cite[!, "dst"])
#
# cd(data_path_tmp)
# df_ipc = CSV.read("ipcs.csv")
# cd(data_path_full)
#
# df1 = make_df(df_cite, df_grants, df_firm_grant)
# df1 = add_ipc(df1, df_ipc)
# df2 = drop_missings(df1)
# df3 = rm_self_citations(df2)
# df4 = make_unique(df3)
## Loading finished data

cd(data_path_tmp)
df1 = CSV.read("df1.csv")
df2 = CSV.read("df2.csv")
df3 = CSV.read("df3.csv")
df4 = CSV.read("df4.csv")

## Calculating and plotting
# plot_ratios(df4, df1, "Triangles/Total Citations", "1")

overall = count_trs(df4, df2)

## Plotting different measures

# Differentiating by field and technlogy respectively
technology_results = count_by_fields(df3, df2, "technology")
field_results = count_by_fields(df3, df2, "field_num")

# Functions for plotting
function absolute_triples(df::DataFrame)

    trace1 = scatter(df, x = :year, y = :trs_discrete, mode="lines", name="discrete triples")

    trace2 = scatter(df, x = :year, y = :trs_complex, mode="lines", name="complex triples")

    layout = Layout(;title="Absolute number of triples")
    data = [trace1, trace2]
    plot(data, layout)
end

function yoy_triples(df::DataFrame)
    year_list = sort(unique(df[!, "year"]))
    yoy_discrete = un_cumulate(df[!,"trs_discrete"])
    yoy_complex = un_cumulate(df[!,"trs_complex"])

    trace1 = bar(;x=year_list, y=yoy_discrete, name="discrete triples", opacity=0.5)

    trace2 = bar(;x=year_list, y=yoy_complex, name="complex triples", opacity=0.5)

    layout = Layout(;title="YoY increase in number of triples")
    data = [trace1, trace2]
    plot(data, layout)
end

function trs_over_cites(df::DataFrame)

    y1 = df[!,"trs_discrete"]./df[!,"cites_discrete"]
    y2 = df[!,"trs_complex"]./df[!,"cites_discrete"]

    trace1 = scatter(df, x = :year, y = y1, mode="lines", name="discrete triples")

    trace2 = scatter(df, x = :year, y = y2, mode="lines", name="complex triples")

    layout = Layout(;title="Triples relative to total citations")
    data = [trace1, trace2]
    plot(data, layout)
end

# Get plots
absolute_triples(technology_results)
yoy_triples(technology_results)
trs_over_cites(technology_results)

# Table for triples by industry share
by_field = field_results[size(field_results,1),collect(2:2:size(field_results,2))]
by_field_arr = convert(Array{Int64}, by_field)
table_df = DataFrame(field_num = 1:35)
table_df[!, "triples"] = zeros(35)
table_df[1:6, "triples"] = by_field_arr[1:6]
table_df[8:10, "triples"] = by_field_arr[7:9]
table_df[12:35, "triples"] = by_field_arr[10:33]

table_df[!, "ratio"] = table_df[!,"triples"]./sum(by_field_arr)

df_edit = unique(df4, "field_num")

out = leftjoin(table_df, df_edit[!,["field_num", "field"]], on = :field_num)
out = out[[:field_num, :field, :triples, :ratio]]
sort!(out, :field_num)
rename!(out, "ratio" => "share")
println(out)


# How many triples go lost?
sum(by_field_arr)/overall[1][25]
sum(technology_results[25, ["trs_discrete", "trs_complex"]])/overall[1][25]

## Playground

df_tmp = df3[df3[!,"field_num"].==13,:]
abc, def = count_trs(df_tmp, df2)
