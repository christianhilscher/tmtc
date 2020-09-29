import pandas as pd 
from bokeh.plotting import figure, output_notebook, show
from bokeh.io import export_png
from bokeh.models import NumeralTickFormatter

output_notebook()

#**************
#! FUNCTIONS
#**************

def tech_plot(x, total, disc, com, title, ylab, xlab = "Year"):
    """
    Function to create plots with total, discrete and complex data.
    """
    plot = figure(plot_width = 500, plot_height = 500, x_axis_label = xlab,
                y_axis_label = ylab, title = title)
    plot.line(x, total, color = "blue", legend_label = "total")
    plot.line(x, disc, color = "red", legend_label = "discrete")
    plot.line(x, com, color = "orange", legend_label = "complex")
    plot.legend.location = "top_left"
    return(plot)

def barplot(top, title, ylab, x, ticks, xlab = "Technology Field"):
    """
    Create vbarplots for share of citations across fields in different variations.
    """
    plot = figure(plot_width = 500, plot_height = 500,
                title = title,
                x_axis_label = xlab, y_axis_label = ylab)
    plot.vbar(x = x, top = top, width = 0.9)
    plot.xaxis.ticker = list(ticks.keys())
    plot.xaxis.major_label_overrides = ticks
    plot.xaxis.major_label_orientation = 0.8
    return(plot)

#**************
#! DATA
#**************
thickets = pd.read_csv("output/tmp/thickets.csv")
cits = pd.read_csv("output/tmp/cits.csv")
tris = pd.read_csv("output/tmp/tris.csv")

triads = pd.read_csv("output/tmp/triads.csv")

#**************
#! PLOTS
#**************

#*Denominator and Numerator of thickets and thickets 
x = np.arange(1976, 2001)
y1 = tris["complete"]
y2 = cits["complete"]
y3 = thickets["complete"]
y4 = thickets["discrete"]
y5 = thickets["complex"]

plot = figure(plot_width = 800, plot_height = 500, x_axis_label = "Year", 
                y_axis_label = "count", title = "Citations and Triangles")
plot.line(x, y1, color = "blue")
plot.line(x, y2, color = "red")
show(plot)
plot = figure(plot_width = 800, plot_height = 500, x_axis_label = "Year", 
                y_axis_label = "count", title = "Thickets")
plot.line(x, y3, color = "orange", legend_label = "complete")
plot.line(x, y4, color = "blue", legend_label = "discrete")
plot.line(x, y5, color = "red", legend_label = "complex")
show(plot)

