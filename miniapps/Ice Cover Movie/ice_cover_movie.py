import streamlit as st
import pandas as pd
import numpy as np
import requests
from pathlib import Path
import datetime
import os
import imageio
import io
import requests
import matplotlib.pyplot as plt
import matplotlib as mpl
import calendar
import base64
import random

@st.cache
def download_sea_ice_extent(localpath="./sun"):
    Path(localpath).mkdir(exist_ok=True,parents=True)
    try:
        filename = os.path.join(localpath,"N_seaice_extent_daily_v3.0.parquet")
    except:
        pass
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
        df.to_parquet(filename)
    return df

@st.cache
def get_dates(method,month,df):
    years = range(df.year.min(),df.year.max()+1)
    dates = []
    extents = []

    if method == "1st day of month":
        for y in years:
            ddf = df[(df.year == y)&(df.month == month)&(df.day == 1)]
            if len(ddf) > 0:
                dates.append(datetime.date(y,month,1))
                extents.append(ddf.extent.values[0])
    elif method == "15 of the month":
        for y in years:
            ddf = df[(df.year == y)&(df.month == month)&(df.day == 15)]
            if len(ddf) > 0:
                dates.append(datetime.date(y,month,15))
                extents.append(ddf.extent.values[0])
    elif method == "last day of month":
        for y in years:
            day = calendar.monthrange(y,month)[1]
            ddf = df[(df.year == y)&(df.month == month)&(df.day == day)]
            if len(ddf) > 0:
                dates.append(datetime.date(y,month,day))
                extents.append(ddf.extent.values[0])
    elif method == "lowest extent in month":
        ddf = df[df.month == month]
        for y in years:
            if len(ddf[ddf.year == y]) > 0:
                dates.append(ddf[ddf.year == y].extent.idxmin().date())
                extents.append(ddf.loc[ddf[ddf.year == y].extent.idxmin()].extent)
    elif method == "largest extent in month":
        ddf = df[df.month == month]
        for y in years:
            if len(ddf[ddf.year == y]) > 0:
                dates.append(ddf[ddf.year == y].extent.idxmax().date())
                extents.append(ddf.loc[ddf[ddf.year == y].extent.idxmax()].extent)
    else:
        assert False
    
    return dates,extents


def provide_gif_download_link(filename):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    with open(filename,"rb") as imagefile:
        b64 = base64.b64encode(imagefile.read()).decode()  # some strings <-> bytes conversions necessary here
        href = f'<a href="data:image/gif;base64,{b64}">Download gif file</a>'

    return href

 
def download_directory(progressbar,dates,localpath):
    Path(localpath).mkdir(exist_ok=True,parents=True)

    i = 0
    images = []
    #for year in range(1987,datetime.date.today().year+1):
    for refdate in dates:
        i += 1
        progress = int(max(0,min(1,i/(datetime.date.today().year+1-1987)))*100)
        progressbar.progress(progress)
        #for m in [month]:
        #    refdate = datetime.date(year,m,15)
        if os.path.exists(os.path.join(localpath,"N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate))):
            images.append(imageio.imread(os.path.join(localpath,"N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate))))
            #print(os.path.join(localpath,"N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate)))
            continue
        url = "http://masie_web.apps.nsidc.org/pub/DATASETS/NOAA/G02135/north/daily/images/{:%Y}/{:%m}_{:%b}/".format(refdate,refdate,refdate)
        file = "N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate)
        r = requests.get(url+file)
        if r.ok:
            try:
                with open(os.path.join(localpath,"N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate)),"w+b") as imagefile:
                    imagefile.write(r.content)
                images.append(imageio.imread((os.path.join(localpath,"N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate)))))
            except:
                os.remove(os.path.join(localpath,"N_{:%Y%m%d}_extn_blmrbl_v3.0.png".format(refdate)))

    Path("./mercury").mkdir(exist_ok=True,parents=True)
    imageio.mimwrite('./mercury/sea_ice_animation.gif', images, fps=1.,subrectangles=True)
    st.sidebar.success("Downloaded requested images and created animated gif")


st.header("""Arctic ice cover over the past three decades""")

st.markdown(body="""We have heard about it. But seeing it yourself, and getting a feel for the data is much better. 
    This notebook downloads northern hemisphere satellite images.""")

with st.spinner("Downloading sea ice extent data from http://masie_web.apps.nsidc.org"):
    df = download_sea_ice_extent()
    ice_extents = ddf = df[["month","extent"]].pivot(columns="month",values="extent")
    data = [ddf[m].dropna().values for m in range(1,13)]
st.sidebar.success("Updated latest sea ice extent data")

st.subheader('Arctic Sea Ice Extent across the year')

st.markdown("""Obviously, the sea ice extent changes with the season. It reaches its peak at the end of the winter season in March, 
    and its lowest extent towards the end of summer, in September. As it is affected by weather, not just climate, the exact date of the
    annual minima and maxima will vary between years.
    """)



plt.style.use('ggplot')

COLOR = 'white'
mpl.rcParams['text.color'] = COLOR
mpl.rcParams['axes.labelcolor'] = COLOR
mpl.rcParams['xtick.color'] = COLOR
mpl.rcParams['ytick.color'] = COLOR

months = ["{:%B}".format(datetime.date(2021,m,1)) for m in range(1,13)]
monthnum_by_name = dict(zip(months,range(1,13)))
monthname_by_num = dict(zip(months,range(1,13)))



progress = st.sidebar.progress(0)
#download = st.components.v1.html('<a href="data:image/gif" download="./mercury/sea_ice_animation.gif">Download gif file</a>')
#st.components.v1.html(provide_gif_download_link("./mercury/sea_ice_animation.gif"))#, unsafe_allow_html=True)
#st.markdown('<a href="./mercury/sea_ice_animation.gif">Download gif animation</a>', unsafe_allow_html=True)

st.sidebar.markdown("Select the month you want to use to create the animation and the day of the month, or the method to select the day.")
st.sidebar.markdown("For winter comparisons, we recommend _largest extent in month_ and _March_, for summer, _lowest extent in month_ and _September_.")
select_month = st.sidebar.select_slider(label="Month",options=months,value="September")
select_day_method = st.sidebar.radio("Which day should we retrieve",options=["1st day of month","15 of the month","last day of month",
    "lowest extent in month","largest extent in month"])
display_data = st.sidebar.empty()

seasonal = st.empty()

fig, ax = plt.subplots()
fig.set_figheight(2.5)
fig.set_figwidth(10)
ax.boxplot(data)
ax.set_xticklabels(["{:%b}".format(datetime.date(2021,m,1)) for m in range(1,13)])
plt.xlabel("Month of the Year")
plt.ylabel("Sea Ice Extent [1E6 km^2]")
plt.title("Seasonal variation of Arctic Sea Ice Cover")
fig.patch.set_facecolor('#3A3A4A')
#st.pyplot(fig)
seasonal.pyplot(fig)

trend = st.empty()
earth = st.empty()


with st.spinner("Downloading image files"):
    earth.image("./clear.gif")
    dates,extents = get_dates(select_day_method,monthnum_by_name[select_month],df)
    download_directory(progress,dates,"./sun/NOAA/G02135/north/daily/images")
    earth.image("./mercury/sea_ice_animation.gif")
    fig2, ax2 = plt.subplots()
    fig2.set_figheight(2.5)
    fig2.set_figwidth(10)
    ax2.scatter(dates,extents,s=50,marker="+")
    plt.xlabel("Year")
    plt.ylabel("Sea Ice Extent [1E6 km^2]")
    plt.title("Sea Ice Extent for {} of {}".format(select_day_method,select_month))
    fig2.patch.set_facecolor('#3A3A4A')
    trend.pyplot(fig2)

    display_data.dataframe(df.loc[dates][["extent"]])
    #download.
#st.image("./mercury/sea_ice_animation.gif")
#st.markdown("![](./mercury/sea_ice_animation.gif)")
#earth_image.html = 
#st.components.v1.html("<img src='./mercury/sea_ice_animation.gif'>")

print(monthnum_by_name[select_month]-1)
print(data[monthnum_by_name[select_month]])
y = extents
x = [monthnum_by_name[select_month]+random.randrange(-10,10)/40. for i in range(len(y))]
ax.scatter(x,y,marker="x",s=15,alpha=0.5)
seasonal.pyplot(fig)
