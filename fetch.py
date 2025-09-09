import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Live Internship Fetcher", layout="wide")
st.title("🌐 Live Internship Fetcher Demo")
st.write("This demo fetches internship listings from a website and shows them in a table.")

# Input: Website URL
url = st.text_input("Enter Internship Website URL", "https://internshala.com/internships")

if st.button("Fetch Internships"):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Example: Extract internship titles (change selector based on site)
        internships = [item.text.strip() for item in soup.find_all("h4", class_="internship-title")]

        if internships:
            df = pd.DataFrame(internships, columns=["Internship Title"])
            st.success(f"Fetched {len(internships)} internships!")
            st.dataframe(df)
        else:
            st.warning("No internships found. You might need to adjust the selector.")

    except Exception as e:
        st.error(f"Error fetching internships: {e}")
