using Pkg
using LightGraphs, MetaGraphs
using CSV, DataFrames
using PlotlyJS

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

cd(data_path_full)
df = CSV.read("uspatentcitation.tsv")
df = dropmissing(df, "date")
df[!, "year"] = first.(df[!, "date"], 4)
df = df[df[!, "year"].<2000, :]

df_refs = CSV.read("otherreference.tsv")

df_firm_grant = CSV.read("grant_firm.csv")
df_grants = CSV.read("grant_grant.csv")
df_cite = CSV.read("grant_cite.csv")

abc = innerjoin(df_cite, df, on = :src => :patent_id)
