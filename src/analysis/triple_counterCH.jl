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
"""
Takes a graph object as input and only returns those neighbors who cite both ways
"""
function make_undirected(graph::SimpleDiGraph)

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

function addtograph!(graph::SimpleDiGraph, srcs, dsts)

    for (i, el) in enumerate(srcs)
        add_edge!(graph, srcs[i], dsts[i])
    end
end


function count_triangles(df::DataFrame, df_citations::DataFrame)

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
        addtograph!(G_directed, df_rel[!,"firm_src"], df_rel[!,"firm_dst"])

        # Keeping only those where the connection goes both ways
        T_vec = make_undirected(G_directed)
        for (i, el) in enumerate(T_vec)
            add_edge!(G_undirected, T_vec[i])
        end

        # Counting triangles in that graph only containing both directions
        tmp = triangles(G_undirected)
        trs[ind] = sum(tmp)/3
        #cts[ind] = length(unique(df_rel_cites[!, :srcdst]))
        cts[ind] = ne(G_directed)
    end

    # Since the triangles add up over the years also use the cumulative sum for citations
    return trs, cts
end

function plot_ratios(df::DataFrame,
                    df_cites::DataFrame,
                    title::String,
                    name::String)

    xs = sort(unique(df[!,"year"]))
    triangles, cites = count_triangles(df, df_cites)

    ratio = triangles./cites
    plot(xs, ratio, title=title, label = "ratio")
    savefig(join([graph_path, name, ".png"]))
end

function linescatter1(df::DataFrame)
    trace1 = scatter(df, x = :year_list, y = :ratio_d, mode="lines", name="discrete industries")

    trace2 = scatter(df, x = :year_list, y = :ratio_c, mode="lines", name="complex industries")

    plot([trace1, trace2])
end

"""
Counting triangles but differentiating by some variable first.
"""
function count_by_fields(df::DataFrame,
                        df_citations::DataFrame,
                        variable::String)

    categories = sort(unique(df[!, variable]))

    xs = sort(unique(df_citations[!,"year"]))
    df_hold = DataFrame(year = xs)

    for (ind, cat) in enumerate(categories)
        println(cat)
        # Making names for dataframe
        name1 = join(["trs_", cat])
        name2 = join(["cites_", cat])

        # Conditional counting
        x1, x2 = count_triangles(df[df[!,variable].==cat,:], df_citations)
        df_hold[!, name1] = x1
        df_hold[!, name2] = x2

    end
    return df_hold
end

function uncumulate(arr::Vector{Int64})
    n = length(arr)
    out = zeros(n)

    for i in reverse(range(2,stop=n))
        out[i] = arr[i] - arr[i-1]
    end
    return out
end

# Loading finished data

cd(data_path_tmp)
df1 = CSV.read("df1.csv")
df2 = CSV.read("df2.csv")
df3 = CSV.read("df3.csv")
df4 = CSV.read("df4.csv")
CSV.write("df4.csv", df4)
## Calculating and plotting
# plot_ratios(df4, df1, "Triangles/Total Citations", "1")

overall = count_triangles(df4, df2)
## Plotting different measures

# Differentiating by field and technlogy respectively
technology_results = count_by_fields(df3, df3, "technology")
field_results = count_by_fields(df3, df2, "subcategory_id")

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
    yoy_discrete = uncumulate(df[!,"trs_discrete"])
    yoy_complex = uncumulate(df[!,"trs_complex"])

    trace1 = bar(;x=year_list, y=yoy_discrete, name="discrete triples", opacity=0.5)

    trace2 = bar(;x=year_list, y=yoy_complex, name="complex triples", opacity=0.5)

    layout = Layout(;title="YoY increase in number of triples")
    data = [trace1, trace2]
    plot(data, layout)
end

function trs_over_cites(df::DataFrame)

    y1 = df[!,"trs_discrete"]./(df[!,"cites_discrete"]+df[!,"cites_complex"])
    y2 = df[!,"trs_complex"]./(df[!,"cites_discrete"]+df[!,"cites_complex"])

    trace1 = scatter(df, x = :year, y = y1, mode="lines", name="discrete triples")

    trace2 = scatter(df, x = :year, y = y2, mode="lines", name="complex triples")

    trace3 = scatter(df, x = :year, y = y1+y2, mode="lines", name="total triples")

    layout = Layout(;title="Triples relative to total patents")
    data = [trace1, trace2, trace3]
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

# Analysis by NBER subcategory instead of IPC

# by_field = field_results[size(field_results,1),collect(2:2:size(field_results,2))]
# by_field_arr = convert(Array{Int64}, by_field)
#
# table_df = DataFrame(subcategory_id = sort(unique((df3[!, "subcategory_id"]))))
# table_df[!, "triples"] = by_field_arr
# table_df[!, "ratio"] = table_df[!,"triples"]./sum(by_field_arr)
#
# df_edit = unique(df4, "subcategory_id")
#
# out = leftjoin(table_df, df_edit[!,["subcategory_id", "subcategory_title"]], on = :subcategory_id)
# out = out[[:subcategory_id, :subcategory_title, :triples, :ratio]]
# sort!(out, :subcategory_id)
# rename!(out, "ratio" => "share")
# println(out)
technology_results[:,:cites] = technology_results[:,:cites_discrete] + technology_results[:,:cites_complex]
println(technology_results[:,[:year, :trs_discrete, :trs_complex, :cites_discrete, :cites_complex, :cites]])

unique(df3[:,:srcdst])
