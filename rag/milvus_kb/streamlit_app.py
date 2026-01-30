import streamlit as st
import requests

BACKEND_URL = "http://localhost:9090"

st.title("RAG Multi-User Knowledge Base Management")

# --- Fetch user ID list ---
st.sidebar.header("Select Knowledge Base")
response = requests.get(f"{BACKEND_URL}/api/users")
user_ids = response.json().get("users", [])
user_ids.insert(0, "admin")  # Public knowledge base first

selected_user = st.sidebar.selectbox("Select a user or admin (public KB)", user_ids)

# --- Fetch file list ---
def fetch_file_list(user):
    if user == "admin":
        resp = requests.get(f"{BACKEND_URL}/api/public_files")
    else:
        resp = requests.get(f"{BACKEND_URL}/api/user_files", params={"user_id": user})
    return resp.json().get("files", [])

if st.sidebar.button("Refresh File List"):
    st.session_state["files"] = fetch_file_list(selected_user)

if "files" not in st.session_state:
    st.session_state["files"] = fetch_file_list(selected_user)

st.subheader(f"{'Public Knowledge Base' if selected_user == 'admin' else 'User ' + selected_user} File List")

files = st.session_state["files"]
if files:
    for f in files:
        st.write(f"- `{f['source']}` - {f['chunk_count']} chunks")
else:
    st.write("No files found")

# --- Upload file ---
st.subheader("Upload File")
uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "txt"])
if uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    if selected_user == "admin":
        res = requests.post(f"{BACKEND_URL}/admin/upload", files=files)
    else:
        data = {"user_id": selected_user}
        res = requests.post(f"{BACKEND_URL}/user/upload", files=files, data=data)

    if res.status_code == 200:
        st.success("Upload successful")
    else:
        st.error("Upload failed")
    # Auto-refresh
    st.session_state["files"] = fetch_file_list(selected_user)

# --- Delete file ---
st.subheader("Delete File")
filename_to_delete = st.text_input("Enter filename to delete (e.g., test.pdf)")
if st.button("Delete File"):
    if selected_user == "admin":
        data = {"source_name": filename_to_delete}
        res = requests.post(f"{BACKEND_URL}/admin/delete", data=data)
    else:
        data = {"user_id": selected_user, "source_name": filename_to_delete}
        res = requests.post(f"{BACKEND_URL}/user/delete", data=data)

    if res.status_code == 200:
        st.success("Deletion successful")
    else:
        st.error("Deletion failed")
    # Auto-refresh
    # st.session_state["files"] = fetch_file_list(selected_user)
