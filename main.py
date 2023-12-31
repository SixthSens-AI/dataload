import streamlit as st

st.set_page_config(
    page_title="Data Load | SixthSens AI",
    page_icon="https://static.thenounproject.com/png/4998583-200.png",
    layout="wide",  # centered, wide
)

hide_streamlit_style = """
            <style>
            .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
            .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
            .viewerBadge_text__1JaDK {display: none;}
            MainMenu {visibility: hidden;}
            header { visibility: hidden; }
            footer {visibility: hidden;}
            #GithubIcon {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

import pandas as pd
import json
import re
import redis
import uuid


# Connect to Redis
hostname = 'redis-13570.c305.ap-south-1-1.ec2.cloud.redislabs.com'
port = '13570'
password = 'wMDKrOv3lzrwQUkJV16DXKR3Jble9V4l'

redis_client = redis.Redis(host=hostname, port=port, password=password)


def process_raw_json(raw_content):
    # Read lines from the content
    lines = raw_content.splitlines()

    # Accumulate lines to form complete JSON objects
    processed_data = []
    current_object = ''
    for line in lines:
        line = line.strip()
        # Accumulate lines to form complete JSON objects
        current_object += line
        if line.endswith('}'):
            try:
                # Load the JSON object and append it to the list
                processed_data.append(json.loads(current_object))
                current_object = ''  # Reset for the next object
            except json.JSONDecodeError as e:
                print(f"Error: {e} - Line: {line}")

    return processed_data

# Create a file uploader
uploaded_file = st.file_uploader("Choose a JSON file", type="json")


# Check if a file has been uploaded
if uploaded_file is not None:
    load_data_button = st.button("Load the Data from Uploaded File")

    if load_data_button:
       # Extract date from file name
        match = re.search(r'\d{2}[A-Za-z]{3}', uploaded_file.name)
        if match is not None:
            date = match.group(0)
        else:
            date = "Not Found"


        # Load the JSON data
        raw_content = uploaded_file.read().decode('utf-8-sig')
        processed_data = process_raw_json(raw_content)

        # Convert to DataFrame
        df = pd.DataFrame(processed_data)

        # Add date to DataFrame as the first column
        if date is not None:
            df.insert(0, 'Date', date)

        # Write DataFrame to Redis
        for _, row in df.iterrows():
            unique_id = str(uuid.uuid4())  # Generate a unique ID for each row
            redis_client.hset('data', unique_id, json.dumps(row.to_dict()))

# Add a button to clear data
if st.button('Clear Data'):
    redis_client.delete('data')

# Load data from Redis
data = redis_client.hgetall('data')
data = [json.loads(v) for v in data.values()]
df = pd.DataFrame(data)

# Display data (last entries first)
st.table(df.iloc[::-1])
