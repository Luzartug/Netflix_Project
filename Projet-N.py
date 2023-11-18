# --- IMPORTS ---
from re import T
from turtle import width
from zipfile import ZipFile as zipfile
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

#image function
def get_image(image):
    img = Image.open(image)
    st.image(img,width=500)

#title
#logo
get_image('assets/Netflix_logo.svg')

#Title
st.title('***Netflix analysis app***')

#Explanation about the project
st.markdown("Netflix is an online streaming platform which will store a huge amount of data about you. In this project you will see your personal data more accessible and understandable. \
    This app will help you to analyse your data and get some insights about your watching habits.  \n"
    "\n You can download your Netflix Data [**Here in your Netflix settings**](https://www.netflix.com/youraccount): Go to **Your Account** and then **Download your data**")
    
with st.expander("General Information"):
    st.markdown("My name is Lucas PASCAL. I'm french student in Data & AI at Panthéon Assas University. \
        In this short project (almost 2 weeks), I wanted to show you the power of data vizualition on your Netflix data.  \n\
        It would be nice to have any feedback or review about this project. \
        Do not hesitate to reach me on [my LinkedIn/Lucas/PASCAL](https://www.linkedin.com/in/lucas222pascal)")

with st.expander("Informations about your data"):
    st.markdown("Q1. **Where is my data stored when I upload it on the website ?**  \n"
        "A1. We are using a open-source app called [Streamlit](https://docs.streamlit.io/knowledge-base/using-streamlit/where-file-uploader-store-when-deleted). \n"
        "Files are stored in memory but Streamlit removes a file from memory when: \n"
        "- The user uploads another file, replacing the original one. \n" 
        "- The user clears the file uploader. \n"
        "- The user closes the browser tab where they uploaded the file.")


#**********************************************************************************************************************

viewing_df = pd.read_csv('assets/ViewingActivity.csv')
billing_hist_df = pd.read_csv('assets/BillingHistory.csv')

#**********************************************************************************************************************
#Time function
def get_sec(dt): return dt.second
def get_min(dt): return dt.minute
def get_hour(dt): return dt.hour
def get_weekday(dt): return dt.weekday()
def get_month(dt): return dt.month
def to_sec(dt): return dt.second + dt.minute*60 + dt.hour*3600

#Function to convert the durationseconds in DAYS:HOURS:MINUTES:SECONDS
def get_time(tot_second):
    sec = timedelta(seconds=int(tot_second))
    d = datetime(1,1,1) + sec
    return "%d:%d:%d:%d" % (d.day-1, d.hour, d.minute, d.second)

#**********************************************************************************************************************
#Sidebar (upload data & informations)
st.sidebar.title('Netflix data')
file_name = st.sidebar.file_uploader("Import your Netflix data", type="zip")

#Add more informations
if file_name is not None:
    with zipfile(file_name, 'r') as myzip:
        myzip.extractall()
        viewing_df = pd.read_csv('./ViewingActivity.csv')
        billing_hist_df = pd.read_csv('./BillingHistory.csv')

#**********************************************************************************************************************
#Data duration preparation

# adding all dataframes into a list
new_columns = [viewing_df]
#add replace all spaces in column titles with underscore
for rename_columns in (new_columns):
    rename_columns.columns = rename_columns.columns.str.replace(' ', '_')

#viewing_df = viewing_df['Supplemental_Video_Type'].isnull()

#Convert in to_datetime
viewing_df['Start_Time']=viewing_df['Start_Time'].map(pd.to_datetime)
viewing_df["Duration"] = pd.to_datetime(viewing_df['Duration'], format='%H:%M:%S')
viewing_df["Bookmark"] = pd.to_datetime(viewing_df['Bookmark'], format='%H:%M:%S')

#Creating columns with the duration in seconds, minutes, hours, weekday and total watched in seconds
viewing_df['Total_watched_second'] = viewing_df['Duration'].map(to_sec)
viewing_df['duration_minutes'] = viewing_df['Bookmark'].map(to_sec)

viewing_df['Total_watched_hours'] = viewing_df['Total_watched_second']/3600
viewing_df['watched_weekday'] = viewing_df['Start_Time'].map(get_weekday)
viewing_df['watched_month'] = viewing_df['Start_Time'].map(get_month)
viewing_df['watched_hour'] = viewing_df['Start_Time'].map(get_hour)

#remove all the movie and serie with a duration less than 1 minute
viewing_df = viewing_df[viewing_df['Total_watched_second'] > 30]
#Remove all the unwanted autoplay movies and series added by Netflix as supplement
viewing_df = viewing_df[viewing_df['Supplemental_Video_Type'].isnull()]

#Calculating the total watched time in seconds
total_watched_time = viewing_df['Total_watched_second'].sum()

### calculating total amount billed
costs = billing_hist_df.loc[(billing_hist_df['Pmt Status'] == 'APPROVED') & (billing_hist_df['Final Invoice Result'] == 'SETTLED'), "Gross Sale Amt"].sum()

#**********************************************************************************************************************
#General informations
#total duration(day - hour - min) / total number of episode / total number of movies / Number of devices / country where you logged in / Money spend

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric('Total Titles Watched',viewing_df.Title.nunique())
col2.metric('Number of Devices',viewing_df.Device_Type.nunique())
col3.metric('Countries Logged in', viewing_df.Country.nunique())
col4.metric('Time spend', get_time(total_watched_time))
col5.metric('Amount paid',(str(np.round_(costs.astype(int), decimals=1)) + ' €'))

#***********************************************************************************************************************
#GRAPH 1
st.write("#")
st.subheader("Which accounts watch the most Netflix ?")

df_graph1 = viewing_df.drop(columns=["Duration", "Bookmark", "Start_Time"], axis=1)

#Creating a graph with the total watched time for each account
total_watchtime_df =  df_graph1.groupby(['Profile_Name'],as_index=False).sum().sort_values('Total_watched_hours')
total_watchtime_df['Total_watched_hours'] = total_watchtime_df['Total_watched_hours'].astype(float).round(1)

fig1 = px.bar(total_watchtime_df, x= 'Profile_Name',  y="Total_watched_hours",
             color="Total_watched_hours",
             color_continuous_scale=["rgb(1,1,1)", "rgb(86,77,77)", "rgb(131,16,16)", "rgb(219,0,0)"],
              labels={
                     "Profile_Name": "Netflix Profile Name",
                     "Total_watched_hours": "Total time watched (Hours)"
                 })
st.plotly_chart(fig1, use_container_width=True)


#***********************************************************************************************************************
#GRAPH 2

#What is the most watched movies and series on each accounts
viewing_df["Show_Title"] = [s.partition(":")[0] for s in viewing_df.Title]


viewing_df['percent_watched'] = (viewing_df['Total_watched_second'] / viewing_df['duration_minutes']) * 100
#viewing_df['percent_watched2'] = 5 * round(viewing_df['percent_watched']/5)

# filtering out seasons with the word Saison, Episode
viewing_df["temporary_brackets_removed_title"] = viewing_df['Title'].str.replace('(', '')
viewing_df["Type"] = np.where(viewing_df.temporary_brackets_removed_title.astype(str).str.contains(pat = 'Saison | Season |Épisode', case = False), 'Serie', 'Movie')
#viewing_df = viewing_df.drop('temporary_brackets_removed_title', 1)


# account Multi Select Button
account = viewing_df.Profile_Name.unique()

user_radio1 = st.sidebar.multiselect("Netflix Account", account, account)

# Most watched Movies

film_type = ['Movie', 'Serie']

type_movie_button = st.radio("Movies or Series", film_type)
st.subheader(f"Top 10 of the most watched {type_movie_button}")

if type_movie_button == 'Movie':
    clean_movie_df = viewing_df[(viewing_df["Type"] == 'Movie') & (viewing_df["percent_watched"] > 90)]
    movie_fre_df = clean_movie_df[['Profile_Name', 'Title', 'Type']].groupby(['Profile_Name', 'Title'])['Type'].count().reset_index()
    movie_fre_df.rename(columns = {'Type':'Count'}, inplace = True)
    movie_fre_df = movie_fre_df.sort_values('Count', ascending=False)
    fig2 = px.bar(movie_fre_df[movie_fre_df['Profile_Name'].isin(user_radio1)].head(10),
                         x='Title',
                         y = 'Count', 
                         color = 'Profile_Name',
                         color_discrete_sequence=["rgb(50,205,50)", "rgb(200,0,0)", "rgb(255,165,0)"]
                         )
    fig2.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig2, use_container_width=True)

# Most watched Serie
if type_movie_button == 'Serie':
    clean_serie_df = viewing_df[(viewing_df["Type"] == 'Serie') & (viewing_df["percent_watched"] > 85)]
    serie_fre_df = clean_serie_df[['Profile_Name', 'Show_Title', 'Type']].groupby(['Profile_Name', 'Show_Title'])['Type'].count().reset_index().sort_values('Type', ascending=False)
    serie_fre_df.rename(columns = {'Type':'Count'}, inplace = True)
    fig3 = px.bar(serie_fre_df[serie_fre_df['Profile_Name'].isin(user_radio1)].head(10), 
                        x='Show_Title', 
                        y = 'Count', 
                        color = 'Profile_Name',
                        color_discrete_sequence=["rgb(50,205,50)", "rgb(200,0,0)", "rgb(255,165,0)"])
    fig3.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig3, use_container_width=True)

#***********************************************************************************************************************
#GRAPH 3

st.subheader("Number of hours spend on Netflix each weekend")

viewing_df["watched_weekday2"] = viewing_df['Start_Time'].dt.day_name()

viewing_df['watched_weekday2'] = pd.Categorical(viewing_df['watched_weekday2'], categories=
["Monday","Tuesday", "Wednesday","Thursday", "Friday", "Saturday", "Sunday"],
ordered=True)
    
hours_by_weekday = viewing_df.groupby('watched_weekday2')['Total_watched_hours'].sum()

hours_by_weekday=hours_by_weekday.sort_index()
st.plotly_chart (px.bar((hours_by_weekday)))


#***********************************************************************************************************************
#GRAPH 4

st.subheader("What is the device you use the most to watch Netflix ?")

word_count_device = viewing_df[viewing_df['Profile_Name'].isin(user_radio1)].Device_Type.str.split(expand=True).stack().value_counts()
map_count_df = word_count_device.to_frame()
map_count_df.reset_index(inplace=True)
map_count_df = map_count_df.rename(columns = {'index':'sub_device', 0:'Count'})

devices = ['tv', 'phone', 'ipad', 'tablet', 'pc', 'mac', 'iphone', 'chromecast'] 

# selecting rows based on condition 
devices_df = map_count_df[map_count_df['sub_device'].str.lower().isin(devices)] 

device_and_categories = {'TV': 'TV','iPad': 'Tablet', 'PC': 'PC', 'Chromecast': 'TV', 
                        'MAC': 'PC', 'iPhone': 'Phone', 'Tablet': 'Tablet', 'Phone':'Phone'}

devices_df['Device'] = devices_df['sub_device'].map(device_and_categories)
devices_df.reset_index(drop=True, inplace=True)
devices_df = devices_df.drop(['sub_device'], axis = 1)

devices_df = devices_df.groupby(['Device']).sum(['count']).reset_index().sort_values(['count'])

fig4 = px.bar(devices_df, x= 'Device',
            y="count",
            color='count',
            color_continuous_scale=["rgb(1,1,1)", "rgb(86,77,77)", "rgb(131,16,16)", "rgb(219,0,0)"])
st.plotly_chart(fig4, use_container_width=True)


#***********************************************************************************************************************
#GRAPH 5

st.subheader("Where do you watch Netflix the most ?")

code_df = pd.read_csv('assets/countries_iso.csv', header=None, names=['Country', 'iso_2', 'iso_3', 'UN_Code'])

streaming_country_df = viewing_df[viewing_df['Profile_Name'].isin(user_radio1)].groupby(by='Country', as_index=False).agg({'Start_Time': pd.Series.nunique})
streaming_country_df['Country'] = streaming_country_df['Country'].astype(str).str[0:2]
streaming_country_df = streaming_country_df.merge(code_df,how='inner',left_on=['Country'],right_on=['iso_2'])

fig5 = px.choropleth(streaming_country_df,
                        locations='iso_3',
                        scope="europe",
                        color= 'Start_Time',
                        color_continuous_scale=["rgb(1,1,1)", "rgb(86,77,77)", "rgb(131,16,16)", "rgb(219,0,0)"],
                        hover_name= 'Country_y',
                        projection= 'natural earth',
                        range_color=[0,streaming_country_df['Start_Time'].max()],
                        labels={'Start_Time':'Hours Series/Movies Watched'}
                        )
st.plotly_chart(fig5)

#***********************************************************************************************************************
#GRAPH 6


#preparing data for the graph
heatmap_df = viewing_df[['Start_Time','Profile_Name','watched_weekday','watched_weekday2','watched_hour']]

#dataframe with groupby for the heatmap
heatmap_total_df = heatmap_df.groupby(['watched_weekday','watched_weekday2', 'watched_hour', 'Profile_Name']).size().reset_index(name='W')
heatmap_df = heatmap_total_df.pivot_table(values='W', index=['watched_hour', 'Profile_Name'], columns=['watched_weekday2'])
account2 = heatmap_df.index.get_level_values('Profile_Name').unique()

user_button = st.radio("Netflix Account", account2)
st.subheader(f"When does {user_button} like to watch Netflix?")

fig6, ax = plt.subplots(figsize=(20,20))
gradient = LinearSegmentedColormap.from_list('black_red', ['white', 'darkgrey', 'darkred', 'red'])
sns.heatmap(heatmap_df[heatmap_df.index.get_level_values('Profile_Name').isin([user_button])].droplevel(1, axis=0),
            annot=True, fmt='g', cmap=gradient, ax=ax)

ax.set_xlabel('Weekday', fontsize=15)  
ax.set_ylabel('Time spend', fontsize=15) 
st.pyplot(fig6)


with st.expander("Acknowledgements"):
    st.markdown("I would like to express my gratitude to my dear supervisor, **Dr Mano Mathew**, who guided me throughout this project.  \n \
    I would also like to thank my love AG who supported me and offered deep insight into the study.  \n\
    Thank you everyone !!")
