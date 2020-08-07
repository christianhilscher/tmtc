using Pkg
using LightGraphs, MetaGraphs
using CSV, DataFrames
using PlotlyJS

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

function make_df(raw_cites::DataFrame,
    raw_grants::DataFrame,
    raw_firms::DataFrame)::DataFrame

    edit_firms = new_ids(raw_firms, "firm_num")
    owner_number = leftjoin(raw_grants, edit_firms, on = :patnum)

    # Getting the owners of the patents
    owner_source = leftjoin(raw_cites, edit_firms, on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, edit_firms, on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    full = leftjoin(owner_number, dst_source, on = :patnum => :src)

    # Adding year from pubdate
    year_list = first.(string.(full[!, "pubdate"]), 4)
    full[!, "year"] = year_list

    return full[!,["patnum", "pubdate", "ipc", "ipcver", "dst", "firm_src", "firm_dst", "year"]]
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

function count_cites(df::DataFrame, type::String)::DataFrame

    cited = Array{Int64}(undef, 1)
    if type == "being_cited"
        unique_pats = groupby(df, :patnum)
        cited = Array{Int64}(undef, length(unique_pats))

        for (ind, el) in enumerate(unique_pats)
            cited[ind] = length(unique(el[!,"dst"]))
        end
    elseif type == "cites"
        unique_pats = groupby(df, :dst)
        cited = Array{Int64}(undef, length(unique_pats))

        for (ind, el) in enumerate(unique_pats)
            cited[ind] = length(unique(el[!,"patnum"]))
        end
    else
        println("Choose either 'cites' or 'being_cited'.")
    end


    return DataFrame(counts = cited)
end

function histo01(xs)
    tr1 = histogram(xs, x = :counts, opacity = 0.8)
    data = [tr1]
    plot(data)
end
###############################################################################

cd(data_path)
df1 = CSV.read("df1.csv")
df2 = CSV.read("df2.csv")
df3 = CSV.read("df3.csv")
df4 = CSV.read("df4.csv")



cites = count_cites(df2, "cites")
print(describe(cites))
histo01(cites)

# Missings
year_ls = sort(unique(df1[!,"year"]))

a = zeros(length(year_ls))
b = zeros(length(year_ls))

for (ind, y) in enumerate(year_ls)

    a[ind] = size(df1[df1[!,"year"].==string(y),:], 1)
    b[ind] = size(dropmissing(df1[df1[!,"year"].==string(y),:]), 1)

end

a1 = cumsum(a)
b1 = cumsum(b)

function linescatter1()
    trace1 = scatter(;x=year_ls, y=a1, mode="lines", name="total citations")

    trace2 = scatter(;x=year_ls, y=b1, mode="lines", name="without missings")

    trace3 = bar(;x=year_ls, y=a1-b1, opacity=0.5, name="missings")
    plot([trace1, trace2, trace3])
end
linescatter1()
unique(df1)

print(names(df3))
