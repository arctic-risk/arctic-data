import streamlit as st
import pandas as pd
import requests
import geopandas as gpd
import urllib
import os
import zipfile
import io
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import datetime

def get_world():
    url = "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_map_subunits.zip"
    DIR = "./sun"+urllib.parse.urlparse(url).path.replace(".zip","").replace("//","/")
    if not os.path.exists(DIR):
        headers = {'User-Agent': 'Arctic Sea Ice'}
        r = requests.get(url,headers=headers)
        if r.ok:
            zf = zipfile.ZipFile(io.BytesIO(r.content))
        Path(DIR).mkdir(exist_ok=True,parents=True)
        zf.extractall(DIR)

    for f in os.listdir(DIR):
        if ".shp" in f:
            gdfWorld = gpd.read_file(os.path.join(DIR,f))
            
    return gdfWorld


@st.cache
def download_sea_ice_extent(localpath="./sun"):
    filename = os.path.join(localpath,"N_seaice_extent_daily_v3.0.parquet")
    download = True
    if os.path.exists(filename):
        df = pd.read_parquet(filename)
        print((datetime.datetime.now()-df.index.max()).days,"DAYS OLD")
        if (datetime.datetime.now()-df.index.max()).days < 1:
            download = False
        else:
            download = True
    if download:
        url = "http://masie_web.apps.nsidc.org/pub/DATASETS/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v3.0.csv"
        r = requests.get(url)
        df = pd.read_csv(io.StringIO(r.text),skiprows=[1],header=0)
        for c in df.columns:
            df.rename(columns={c:c.strip().lower()},inplace=True)
        df.index = pd.to_datetime(df[["year","month", "day"]])
        del df["source data"]
        # clip incomplete 1978 data else things are confusing
        df = df[df.year > 1978]
        df.to_parquet(filename)
    return df


def load_ice_extent_shapefile(year,month):
    refdate = pd.to_datetime("{}-{}-15".format(year,month))
    url = "http://masie_web.apps.nsidc.org/pub/DATASETS/NOAA/G02135/north/monthly/shapefiles/shp_extent/{:%m}_{:%b}/extent_N_{:%Y%m}_polygon_v3.0.zip".format(refdate,refdate,refdate)
    DIR = "./sun"+urllib.parse.urlparse(url).path.replace(".zip","")
    if not os.path.exists(DIR):
        r = requests.get(url)
        if r.ok:
            zf = zipfile.ZipFile(io.BytesIO(r.content))
        Path(DIR).mkdir(exist_ok=True,parents=True)
        zf.extractall(DIR)
        
    for f in os.listdir(DIR):
        if ".shp" in f:
            gdfIceExtent = gpd.read_file(os.path.join(DIR,f))
    
    return gdfIceExtent


def get_ice_extent_shapes(idxOne,idxTwo):
    gdfOne = load_ice_extent_shapefile(idxOne.year,idxOne.month)
    gdfTwo = load_ice_extent_shapefile(idxTwo.year,idxTwo.month)
    return gdfOne,gdfTwo


plt.style.use('ggplot')

COLOR = 'white'
mpl.rcParams['text.color'] = COLOR
mpl.rcParams['axes.labelcolor'] = COLOR
mpl.rcParams['xtick.color'] = COLOR
mpl.rcParams['ytick.color'] = COLOR


st.header("""Arctic ice cover compared to a set of countires""")

#st.sidebar.markdown("![Arctic Basecamp Logo](https://arcticbasecamp.org/wp-content/uploads/2020/06/navigation-logo.png)")
st.sidebar.image("https://arcticbasecamp.org/wp-content/uploads/2020/06/navigation-logo.png")

region = st.sidebar.empty()
subregion = st.sidebar.empty()
select_years_placeholder = st.sidebar.empty()
method = st.sidebar.radio("Which value should we retrieve",options=["Minimum Sea Ice Extent in Year","Maximum Sea Ice Extent in Year"])

st.markdown(body="""We have heard about it. But seeing it yourself, and getting a feel for the data is much better. 
    This notebook downloads northern hemisphere satellite images so you can compare arcitc sea ice extent over
    the years with your part of the world.""")

display_data = st.sidebar.empty()

with st.spinner("Downloading World map from https://www.naturalearthdata.com and sea ice extent data from http://masie_web.apps.nsidc.org"):
    gdfWorld = get_world()
    df = download_sea_ice_extent()
    dfIceExtents = df[["year","extent"]].pivot(columns="year",values="extent")
    data = [dfIceExtents[y].dropna().values for y in dfIceExtents.columns]
    st.sidebar.success("Got world map and updated latest sea ice extent data")
    select_years = select_years_placeholder.slider(label="Compare Years",
        min_value=int(df.year.min()),
        max_value=int(df.year.max()),
        value=(int(df.year.min()),int(datetime.date.today().year-1)),
        step=1)

region_list = region.multiselect("Region",options=sorted(gdfWorld.REGION_UN.unique()),default="Europe")
if len(region_list) > 0:
    available_subregions = sorted(gdfWorld[gdfWorld.REGION_UN.isin(region_list)].SUBREGION.unique())
    print(available_subregions)
    subregion_list = subregion.multiselect("Subregion",options=available_subregions,default=available_subregions)
    #print(available_subregions)
else:
    available_subregions = []
    subregion_list = subregion.multiselect("Subregion",options=available_subregions)
#subregion_list = subregion.multiselect("Subregion",options=available_subregions,default=region_list[0])

annual = st.empty()

st.markdown("""The plot below overlays _{} {}_ in blue, _{} {}_ in red over your chosen selection of subregions, {}. 
    The projection aligns the centroids of the ice extent and world/subregion maps shapes.""".format(
    method, select_years[0],
    method, select_years[1],
    ",".join(subregion_list)
    ))

map_output = st.empty()

fig, ax = plt.subplots()
fig.set_figheight(2.5)
fig.set_figwidth(10)
ax.boxplot(data)
ax.set_xticklabels(["{}".format(y) for y in dfIceExtents.columns])
plt.locator_params(axis='x', nbins=10)

plt.xlabel("Year")
plt.ylabel("Sea Ice Extent [1E6 km^2]")
plt.title("Variation of Arctic Sea Ice Cover over the years")
fig.patch.set_facecolor('#3A3A4A')
annual.pyplot(fig)

with st.spinner("Downloading sea ice extent data from http://masie_web.apps.nsidc.org"):
    print(select_years)
    if "Maximum" in method:
        idxOne = df[df.year == select_years[0]].extent.idxmax()
        idxTwo = df[df.year == select_years[1]].extent.idxmax()
    elif "Minimum" in method:
        idxOne = df[df.year == select_years[0]].extent.idxmin()
        idxTwo = df[df.year == select_years[1]].extent.idxmin()
    #print(df.loc[idxOne])
    #print(df.loc[idxTwo])
    #valueOne = df
    gdfOne,gdfTwo = get_ice_extent_shapes(idxOne,idxTwo)

    ddf = df.loc[[idxOne,idxTwo]][["year","extent"]]
    ddf.index = ddf.year
    del ddf["year"]
    ddf["percentage"] = 1.0
    ddf.at[ddf.index.max(),"percentage"] = ddf.loc[select_years[1]].extent/ddf.loc[select_years[0]].extent
    display_data.dataframe(ddf.style.format({"extent":"{:.2f} mkm²","percentage":"{:.1%}"}))


if len(subregion_list) > 0:
    gdfSubregions = gdfWorld[gdfWorld.SUBREGION.isin(subregion_list)]
    centroid = gdfSubregions.dissolve(by="SUBREGION").centroid
    x = centroid.x
    y = centroid.y
else:
    gdfSubregions = gpd.GeoDataFrame()

fig, ax = plt.subplots()
fig.set_figheight(15)
fig.set_figwidth(15)

if len(subregion_list) > 0:
    ax = gdfSubregions.to_crs("+proj=ortho +lat_0={} +lon_0={} +x_0=0 +y_0=0".format(y[0],x[0])).plot(color="black",alpha=0.99,ax=ax)
    gdfOne.to_crs("+proj=ortho +lat_0=90 +lon_0=0 +x_0=0 +y_0=0").plot(ax=ax,color="steelblue",alpha=0.5)
else:
    ax = gdfOne.to_crs("+proj=ortho +lat_0=90 +lon_0=0 +x_0=0 +y_0=0").plot(color="steelblue",alpha=0.5)

gdfTwo.to_crs("+proj=ortho +lat_0=90 +lon_0=0 +x_0=0 +y_0=0").plot(ax=ax,color="tomato",alpha=0.5)
gdfTwo.to_crs("+proj=ortho +lat_0=90 +lon_0=0 +x_0=0 +y_0=0").boundary.plot(ax=ax,color="tomato",linewidth=1)
gdfOne.to_crs("+proj=ortho +lat_0=90 +lon_0=0 +x_0=0 +y_0=0").boundary.plot(ax=ax,color="steelblue",linewidth=1)

ax.grid = False
fig.patch.set_facecolor('#3A3A4A')
plt.axis("off")

map_output.pyplot(fig)