using Pkg
using CSV, DataFrames


wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

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

function add_suffix(df::DataFrame, cols::Vector{String}, suff::String)

    for i in cols
        df = rename(df, i => join([i, suff]))
    end
    return df
end

function to_int(df::DataFrame, col::String)
    df[!, col] =  tryparse.(Int64, df[!,col])
    df = df[isnothing.(df[!,col]).!=1,:]
    return df
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

function make_df(raw_cites::DataFrame,
                edit_grants::DataFrame,
                raw_firms::DataFrame)

    # ATTENTION : Assiging new firm numbers here; need it for graph later
    # edit_firms = make_ids(raw_firms, "firm_num")

    owner_source = leftjoin(raw_cites, raw_firms, on = :src => :patnum)
    owner_source = rename(owner_source, "firm_num" => "firm_src")

    # Getting the owners of the cited patents
    dst_source = leftjoin(owner_source, raw_firms, on = :dst => :patnum)
    dst_source = rename(dst_source, "firm_num" => "firm_dst")

    rename_cols = filter!(x->x != "patnum", names(edit_grants))
    b_src = add_suffix(edit_grants, rename_cols, "_src")
    b_dst = add_suffix(edit_grants, rename_cols, "_dst")


    dst_source = leftjoin(dst_source, b_src, on = :src => :patnum)
    dst_source = leftjoin(dst_source, b_dst, on = :dst => :patnum)

    return dst_source
end

function add_info(raw_grants::DataFrame, df_ipc::DataFrame, df_nber::DataFrame, df_nber_cat::DataFrame, df_nber_subcat::DataFrame)

    edit_grants = make_year(raw_grants)

    edit_grants = edit_grants[:,[:patnum, :year, :ipc]]
    a = add_ipc(edit_grants, df_ipc)
    b = addnber(a, df_nber, df_nber_cat, df_nber_subcat)

    return b
end

function make_year(df::DataFrame)
    year_list = Vector{String}(undef, size(df, 1))
    year_list = first.(string.(df[!, "pubdate"]), 4)
    df[!, "year"] = year_list
    return df
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

grant_info = CSV.read("df_info.csv")
df1 = make_df(df_cite, grant_info, df_firm_grant)

df12 = to_int(df1, "src")
df13 = to_int(df12, "dst")

df2 = dropmissing(df13)
df3 = rm_self_citations(df2)
df4 = make_unique(df3)


cd(data_path_tmp)
CSV.write("df1.csv", df13)
CSV.write("df2.csv", df2)
CSV.write("df3.csv", df3)
CSV.write("df4.csv", df4)
