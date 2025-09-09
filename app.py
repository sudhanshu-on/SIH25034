import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
# --- File paths ---
STUDENT_FILE = "students.csv"
INTERNSHIP_FILE = "internships.csv"

# --- Load student data safely ---
try:
    students = pd.read_csv(STUDENT_FILE)
    if "Name" not in students.columns or "Skills" not in students.columns:
        students = pd.DataFrame(columns=["Name", "Skills"])
except:
    students = pd.DataFrame(columns=["Name", "Skills"])

# --- Load internship data safely ---
try:
    internships = pd.read_csv(INTERNSHIP_FILE)
    if not set(["Title", "Requirements", "Location", "Mode"]).issubset(internships.columns):
        internships = pd.DataFrame(columns=["Title", "Requirements", "Location", "Mode"])
except:
    internships = pd.DataFrame(columns=["Title", "Requirements", "Location", "Mode"])

# --- Fetch internships from Internshala ---
BASE_URL = "https://internshala.com"

def fetch_internships(url, debug=False):
    internships_list = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        
        cards = soup.find_all("div", class_="individual_internship")
        
        for i, card in enumerate(cards):
            link = card.get("data-href")
            if not link:
                continue
            detail_url = BASE_URL + link
            
            # Visit detail page
            detail_resp = requests.get(detail_url, headers={"User-Agent": "Mozilla/5.0"})
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
            
            # --- Extract title ---
            title_tag = detail_soup.find("h1")  # Most titles are in <h1>
            title = title_tag.text.strip() if title_tag else "N/A"

            # --- Extract skills/requirements ---
            skills = [s.text.strip() for s in detail_soup.find_all("span", class_="round_tabs")]
            requirements = ", ".join(skills) if skills else "N/A"
            
            # --- Extract location from row-1-item locations ---
            # --- Extract location from card (search page) ---
            location = "N/A"
            loc_div = card.find("div", class_=lambda x: x and "location" in x)
            if loc_div:
                location = loc_div.get_text(strip=True)


     
            # --- Determine mode ---
            mode = "Remote" if "work from home" in title.lower() else "In-office"
            
            if debug:
                st.write(f"--- Internship {i+1} ---")
                st.write("Title:", title)
                st.write("Requirements:", requirements)
                st.write("Location:", location)
                st.write("Mode:", mode)
            
            internships_list.append({
                "Title": title,
                "Requirements": requirements,
                "Location": location,
                "Mode": mode
            })
    except Exception as e:
        st.error(f"Error fetching internships: {e}")
    
    return pd.DataFrame(internships_list)

# --- UI ---
st.title("🎓 Internship Recommendation Prototype (Debug Mode)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👨‍🎓 Students",
    "💼 Internships",
    "🌐 Fetch from Web (Debug)",
    "📂 Browse All",
    "🤖 AI Recommendations"
])

# --- Students Tab ---
with tab1:
    st.header("Add Student")
    name = st.text_input("Name")
    skills = st.text_area("Skills (comma separated)")
    if st.button("Save Student"):
        if name and skills:
            new_student = {"Name": name, "Skills": skills}
            students = pd.concat([students, pd.DataFrame([new_student])], ignore_index=True)
            students.to_csv(STUDENT_FILE, index=False)
            st.success("✅ Student added successfully!")

    st.subheader("All Students")
    if students.empty:
        st.info("No students yet. Add one above.")
    else:
        st.dataframe(students)

# --- Internships Tab ---
with tab2:
    st.header("Add Internship")
    title = st.text_input("Internship Title")
    requirements = st.text_area("Requirements (comma separated)")
    location = st.text_input("Location")
    mode = st.selectbox("Mode", ["Remote", "In-office", "Hybrid"])
    
    if st.button("Save Internship"):
        if title and requirements:
            new_internship = {
                "Title": title,
                "Requirements": requirements,
                "Location": location,
                "Mode": mode
            }
            internships = pd.concat([internships, pd.DataFrame([new_internship])], ignore_index=True)
            internships.to_csv(INTERNSHIP_FILE, index=False)
            st.success("✅ Internship added successfully!")

    st.subheader("All Internships")
    if internships.empty:
        st.info("No internships yet. Add one above or fetch from web.")
    else:
        st.dataframe(internships)

# --- Fetch Tab (Debug) ---
with tab3:
    st.header("Fetch Internships from Web (Debug Mode)")
    fetch_url = st.text_input("Enter Internship Website URL")
    if st.button("Fetch Internships"):
        if fetch_url:
            fetched_internships = fetch_internships(fetch_url, debug=True)
            if not fetched_internships.empty:
                internships = pd.concat([internships, fetched_internships], ignore_index=True)
                internships.to_csv(INTERNSHIP_FILE, index=False)
                st.success(f"✅ {len(fetched_internships)} internships fetched and added!")
                st.dataframe(fetched_internships)
            else:
                st.warning("⚠️ No internships found. Adjust selectors if needed.")

# --- Browse/Search Tab ---
with tab4:
    st.header("Browse All Internships")
    search = st.text_input("🔍 Search internships by keyword")
    if search:
        results = internships[internships.apply(lambda row: search.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        st.dataframe(results)
    else:
        st.dataframe(internships)

# --- AI Recommendation Tab ---
with tab5:
    st.header("AI Recommendations")
    if students.empty or internships.empty:
        st.warning("⚠️ Please add students and internships first.")
    else:
        selected_student = st.selectbox("Select a student", students["Name"].tolist())
        student_skills = students[students["Name"] == selected_student]["Skills"].values[0].lower().split(",")

        recommendations = []
        for _, row in internships.iterrows():
            reqs = str(row["Requirements"]).lower()
            matches = sum(skill.strip() in reqs for skill in student_skills)
            recommendations.append((row["Title"], row["Requirements"], row["Location"], row["Mode"], matches))

        rec_df = pd.DataFrame(recommendations, columns=["Title", "Requirements", "Location", "Mode", "Match Score"])
        rec_df = rec_df.sort_values(by="Match Score", ascending=False).reset_index(drop=True)

        st.subheader(f"Top Recommended Internships for {selected_student}")
        st.dataframe(rec_df.head(5))  # Show only top 5 matches
