using Pkg
using CSV, DataFrames

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
seventies = joinpath(data_path, "data_70_89/")
ninties = joinpath(data_path, "data_90_00/")
full = joinpath(data_path, "full/")

cd(ninties)





cd(data_path)

file_list = ["cite_stats", "firm", "grant_cite", "grant_grant", "grant_ipc", "grant_match", "match", "name", "pair", "grant_frim"]

for n in file_list

    sevs = join([seventies, n, ".csv"])
    nins = join([ninties, n, ".csv"])
    out = join([full, n, ".csv"])

    df1 = CSV.read(sevs)
    df2 = CSV.read(nins)


    df3 = vcat(df1, df2)

    CSV.write(out, df3)
end
