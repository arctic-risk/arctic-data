# Create Animated Arctic Sea Ice gif

Use this app to create an animation of arcitc sea ice cover since 1978/1979. Check how much the ice covered area has changed over
time, by looking at annual comparisons of the same months across multiple years.

![](../streamlit-ice_cover_movie.webm)

This app uses [NSIDC Sea Ice Index G02135](https://nsidc.org/data/g02135) data. 

_Fetterer, F., K. Knowles, W. N. Meier, M. Savoie, and A. K. Windnagel. 2017, updated daily._ Sea Ice Index, _Version 3. 
(arctic sea ice extent and arctic sea ice extent blue marble images). Boulder, Colorado USA. NSIDC: National Snow and Ice Data Center. 
[doi: https://doi.org/10.7265/N5K072F8]( https://doi.org/10.7265/N5K072F8)._

## Installation and running

This app uses [pipenv](https://pipenv.pypa.io/en/latest/), a [good guide is here, too](https://realpython.com/pipenv-guide/) to install dependencies.
We need
* streamlit
* pandas, numpy, matplotlib
* [imageio](https://imageio.github.io/) to create the animated gif

## TODO

* add curve fitting and fly-forwarding
* twitter button
* _(most likely not possible) download button for git._ In the mean time, use a right mouse click and download the gif that way.

