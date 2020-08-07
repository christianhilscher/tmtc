using Pkg
using CSV, DataFrames
using XLSX

wd = "/Users/christianhilscher/Desktop/tmtc/"
data_path = join([wd, "data/"])
cd(data_path)

df_ipc = DataFrame(XLSX.readdata("ipc_technology.xls", "Sheet1", "A8:H771"))

df_ipc[!, "x8"] = lowercase.(first.(df_ipc[!, "x8"], 4))

df_ipc[!, "technology"] = repeat(["complex"], size(df_ipc, 1))

for i in range(14, stop=23)
    n = size(df_ipc[df_ipc[!,"x1"].==i,:], 1)
    df_ipc[df_ipc[!,"x1"].==i,"technology"] = repeat(["discrete"], n)
end

select!(df_ipc, ["x1", "x2", "x5", "x8", "technology"])
rename!(df_ipc, [:field_num, :sector, :field, :ipc_code, :technology])

CSV.write("ipcs.csv", df_ipc)
