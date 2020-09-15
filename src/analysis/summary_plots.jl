using Pkg
using LightGraphs, MetaGraphs, SimpleWeightedGraphs
using CSV, DataFrames
using PlotlyJS
using BenchmarkTools, ProgressMeter, Profile
using Random, GraphPlot


wd = pwd()

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

## Functions

function filter_technology(dataf::DataFrame, tech::String)

    cond = dataf[!,:technology_src] .== dataf[!,:technology_dst] .== tech
    return dataf[cond,:]
end

function columnbyyear(dataf_d::DataFrame, dataf_c::DataFrame, dataf_t::DataFrame,  col::String, uni::Int64)

    years = sort(unique(dataf_t[!,:year_src]))
    out = Array{Int64}(undef, length(years), 3)

    if uni==1
        for (ind, y) in enumerate(years)
            out[ind, 1] = length(unique(dataf_d[dataf_d[:year_src] .<= y, col]))
            out[ind, 2] = length(unique(dataf_c[dataf_c[:year_src] .<= y, col]))
            out[ind, 3] = length(unique(dataf_t[dataf_t[:year_src] .<= y, col]))
        end
    else
        for (ind, y) in enumerate(years)
            out[ind, 1] = length(dataf_d[dataf_d[:year_src] .<= y, col])
            out[ind, 2] = length(dataf_c[dataf_c[:year_src] .<= y, col])
            out[ind, 3] = length(dataf_t[dataf_t[:year_src] .<= y, col])
        end
    end

    df_out = DataFrame(:year => years, :value_discrete => out[:,1], :value_complex => out[:,2], :value_total => out[:,3])
    return df_out
end

function plot_summary(df::DataFrame, title::String)
    trace1 = scatter(df, x = :year, y = :value_discrete, mode="lines", name="discrete")
    trace2 = scatter(df, x = :year, y = :value_complex, mode="lines", name="complex")
    trace3 = scatter(df, x = :year, y = :value_total, mode="lines", name="total")

    layout = Layout(;title=title)
    data = [trace1, trace2, trace3]
    plot(data, layout)
end

## Calculating

cd(data_path_tmp)

df3 = CSV.read("df3.csv")

df3[!, "srcdst"] = [(df3[i, :firm_src], df3[i, :firm_dst]) for i in eachindex(df3[!, :firm_src])]
df = df3[df3[!,:year_src] - df3[!,:year_dst] .< 15,:]


df_complex = filter_technology(df, "complex")
df_discrete = filter_technology(df, "discrete")

variable = "srcdst"
title = join(["Cumulative number of unique firm to firm citations; variable: ", variable])

#unique or not
un = 1
data = columnbyyear(df_discrete, df_complex, df, variable, un)

plot_summary(data, title)
