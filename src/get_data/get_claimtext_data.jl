using Pkg
using CSV, DataFrames
using Random

wd = pwd()

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")



## Real data
cd(data_path_tmp)
df3 = CSV.read("df3.csv")

patents = string.(unique!(vcat(df3[!,:src], df3[!,:dst])))
df_pat = DataFrame(:pat_no => patents)
## Claimtexts

cd(join([data_path, "csv/"]))
df_text = CSV.read("patent_claims_fulltext.csv")

a = rand(size(df_text, 1)).<0.1

df_text_small = df_text[a, [:pat_no, :claim_txt]]


ghi = rightjoin(df_pat, df_text_small, on = :pat_no)
