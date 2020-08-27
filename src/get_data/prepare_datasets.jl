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
Recodes the firm_id variable from 1 to n. That's because the graph package only takes vertices from 1 to n and not strings or anything similar
"""
function make_ids(df_firm::DataFrame,
                var::String)

    df_firm = rename(df_firm, var => "tobechanged")
    df_new = df_firm[!, ["tobechanged"]]
    tmp_df = unique(df_new, "tobechanged")
    tmp_df[!, "firm_id"] = 1:size(tmp_df, 1)

    df_new = leftjoin(df_firm, tmp_df, on = :tobechanged)

    df_new = select(df_new, Not(:tobechanged))
    rename!(df_new, "firm_id" => var)

    return df_new
end

"""
Same procedure as with firm ids
"""
function unique_patnum(df::DataFrame)
    tmp_arr = Array(df[!,:patnum])
    append!(tmp_arr, Array(df[!,:dst]))

    unique!(tmp_arr)
    new_ids = collect(1:length(tmp_arr))

    df_lookup = DataFrame(old_patnum = tmp_arr, new_patnum = new_ids)

    df = leftjoin(df, df_lookup, on = :patnum => :old_patnum)
    rename!(df, "new_patnum" => "patnum_integer")

    df = leftjoin(df, df_lookup, on = :dst => :old_patnum)
    select!(df, Not(:dst))
    rename!(df, "new_patnum" => "dst_integer")

    return df
end

"""
Takes the raw data files and merges them into somthing useable
"""
function make_df(raw_cites::DataFrame,
                raw_grants::DataFrame,
                raw_firms::DataFrame)

    edit_firms = make_ids(raw_firms, "firm_num")

    # Getting the owners of the patents
    owner_source = leftjoin(raw_cites, edit_firms, on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, edit_firms, on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    dst_source = leftjoin(dst_source, raw_grants[:,[:pubdate, :patnum, :ipc, :ipcver]], on = :src => :patnum)
    dst_source = rename(dst_source, "src" => "patnum")

    # Adding year from pubdate
    year_list = first.(string.(dst_source[!, "pubdate"]), 4)
    dst_source[!, "year"] = year_list
    dst_source[!, :dst] =  tryparse.(Int64, dst_source[!,:dst])
    dst_source = dst_source[isnothing.(dst_source[!,:dst]).!=1,:]

    # Narrowing it down
    df_out = dst_source[!, [:year, :firm_dst, :firm_src, :ipc, :ipcver, :patnum, :dst]]


    return df_out
end

"""
Adding the ipc classification to the main dataframe
"""
function add_ipc(df::DataFrame,
                df_ipc::DataFrame)

    df_ipc = unique(df_ipc, "ipc_code")

    df = dropmissing(df, "ipc")
    df[!, "ipc_code"] = first.(df[!, "ipc"], 4)
    df_ipc = leftjoin(df, unique(df_ipc, "ipc_code"), on = :ipc_code)

    return df_ipc
end

"""
Adding NBER classification
"""
function addnber(df::DataFrame,
                df_nber::DataFrame,
                df_nber_cat::DataFrame,
                df_nber_subcat::DataFrame)

    # First merging the title categories
    df_cats = leftjoin(df_nber[!,["patent_id", "category_id", "subcategory_id"]], df_nber_cat, on = :category_id => :id)
    df_cats = rename(df_cats, "title" => "category_title")

    df_cats = leftjoin(df_cats, df_nber_subcat, on = :subcategory_id => :id)
    df_cats = rename(df_cats, "title" => "subcategory_title")

    df = leftjoin(df, df_cats, on = :patnum => :patent_id)
    return df
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
    df[!, "srcdst"] = [(df[i, :firm_src], df[i, :firm_dst]) for i in eachindex(df[!, :firm_src])]

    return unique(df, "srcdst")
end


## Reading in and making data

cd(data_path_full)
df_firm_grant = CSV.read("grant_firm.csv")
df_grants = CSV.read("grant_grant.csv")
df_cite = CSV.read("grant_cite.csv")

df_cite = dropmissing(df_cite)

cd(data_path_tmp)
df_ipc = CSV.read("ipcs.csv")
cd(data_path_full)

df_nber = CSV.read("nber.tsv")
df_nber_cat = CSV.read("nber_category.tsv")
df_nber_subcat = CSV.read("nber_subcategory.tsv")

df1 = make_df(df_cite, df_grants, df_firm_grant)
# df11 = unique_patnum(df1)
df12 = add_ipc(df1, df_ipc)
df13 = addnber(df12, df_nber, df_nber_cat, df_nber_subcat)
df2 = drop_missings(df13)
df3 = rm_self_citations(df2)
df4 = make_unique(df3)

## Playground

cd(data_path_tmp)
CSV.write("df1.csv", df13)
CSV.write("df2.csv", df2)
CSV.write("df3.csv", df3)
CSV.write("df4.csv", df4)
