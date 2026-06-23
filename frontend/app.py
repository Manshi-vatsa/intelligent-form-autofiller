import os
import streamlit as st
import requests

st.set_page_config(page_title="Intelligent Form Auto-Filler", page_icon="📄")

st.title("Intelligent Form Auto-Filler")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

uploaded_file = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx", "jpg", "png"]
)

if uploaded_file:
    with st.spinner("Extracting information..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(f"{BACKEND_URL}/extract", files=files)
            response.raise_for_status()
            extracted_data = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error extracting information: {e}")
            st.stop()

    st.subheader("Extracted Information")

    full_name = st.text_input("Full Name", value=extracted_data.get("full_name", ""))
    email = st.text_input("Email", value=extracted_data.get("email", ""))
    phone = st.text_input("Phone", value=extracted_data.get("phone", ""))
    location = st.text_input("Location", value=extracted_data.get("location", ""))
    current_role = st.text_input("Current Role", value=extracted_data.get("current_role", ""))
    total_experience_years = st.text_input(
        "Total Experience (Years)",
        value=extracted_data.get("total_experience_years", "")
    )
    skills = st.text_input(
        "Skills",
        value=", ".join(extracted_data.get("skills", [])) if isinstance(extracted_data.get("skills"), list) else extracted_data.get("skills", "")
    )
    education = st.text_input("Education", value=extracted_data.get("education", ""))
    summary = st.text_area("Summary", value=extracted_data.get("summary", ""))

    if st.button("Submit Application"):
        final_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": location,
            "current_role": current_role,
            "total_experience_years": total_experience_years,
            "skills": [skill.strip() for skill in skills.split(",")] if skills else [],
            "education": education,
            "summary": summary
        }
        
        st.success("Application submitted successfully!")
        st.subheader("Final Application Data")
        st.json(final_data)
