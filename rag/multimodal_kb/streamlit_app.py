import streamlit as st
import requests
import json
from typing import Optional
from pathlib import Path

# -------- CONFIG --------
API_BASE = st.session_state.get("api_base", "http://localhost:8080")  # backend address, adjust if needed
# If img_path is relative and accessible, you can set a base to display images (optional)
IMAGE_BASE = st.session_state.get("image_base", API_BASE)

# -------- HELPERS --------
def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"GET {path} failed: {e}")
        return None

def api_post_multipart(path: str, data: dict = None, files: dict = None):
    try:
        r = requests.post(f"{API_BASE}{path}", data=data or {}, files=files or {}, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"POST {path} failed: {e}")
        return None

def api_post_json(path: str, payload: dict):
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"POST {path} failed: {e}")
        return None

# -------- UI --------
st.set_page_config(page_title="RAG Multi-user KB Manager", layout="wide")
st.title("RAG Multi-user / Admin Knowledge Base Visualization & Control")

# Top-level config
with st.expander("Configuration (modify if backend is not at localhost:9090)", expanded=False):
    api_base_in = st.text_input("Backend API base URL (including protocol and port)", value=API_BASE)
    image_base_in = st.text_input("Image base URL (if img_path is accessible via HTTP)", value=IMAGE_BASE)
    if st.button("Apply configuration"):
        st.session_state["api_base"] = api_base_in.rstrip("/")
        st.session_state["image_base"] = image_base_in.rstrip("/")
        # safe refresh
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            try:
                st.experimental_rerun()
            except Exception:
                st.session_state["_force_refresh"] = not st.session_state.get("_force_refresh", False)

mode = st.sidebar.selectbox("Mode", ["User", "Admin"])

# -------- USER MODE --------
if mode == "User":
    st.subheader("Personal User Knowledge Base")

    # 1. Get user list
    users_resp = api_get("/api/users")
    user_ids = []
    if users_resp:
        if users_resp.get("users") is not None:
            user_ids = users_resp["users"]
        elif users_resp.get("error"):
            st.warning(f"Failed to fetch user list: {users_resp.get('message')}")
    selected_user = st.selectbox("Select user_id", user_ids)

    if selected_user:
        col1, col2 = st.columns([2, 5])

        with col1:
            st.markdown("### File Operations")
            # Upload file
            st.markdown("**Upload a file to this user**")
            uploaded = st.file_uploader("Choose a file to upload (user)", type=None, key="user_upload", accept_multiple_files=False)
            if uploaded:
                if st.button("Start upload", key="upload_user_file"):
                    with st.spinner("Uploading and processing..."):
                        files = {"file": (uploaded.name, uploaded.getbuffer())}
                        data = {"user_id": selected_user}
                        resp = api_post_multipart("/user/upload", data=data, files=files)
                        if resp and not resp.get("error"):
                            st.success(f"Upload succeeded: {uploaded.name}")
                        else:
                            st.error(f"Upload failed: {resp}")
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        try:
                            st.experimental_rerun()
                        except Exception:
                            st.session_state["_force_refresh"] = not st.session_state.get("_force_refresh", False)

            st.markdown("---")
            # Delete by source_name
            st.markdown("**Delete a user file by source_name**")
            user_files_resp = api_get("/api/user_files", params={"user_id": selected_user})
            source_to_delete = None
            if user_files_resp and user_files_resp.get("files"):
                files_list = user_files_resp["files"]
                source_to_delete = st.selectbox("Select source_name to delete", files_list, key="del_user_source")
                if st.button("Delete selected source", key="del_user_btn"):
                    with st.spinner("Deleting..."):
                        data = {"user_id": selected_user, "source_name": source_to_delete}
                        resp = api_post_multipart("/user/delete", data=data)
                        if resp and not resp.get("error"):
                            st.success(f"Deleted: {source_to_delete}")
                        else:
                            st.error(f"Deletion failed: {resp}")
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        try:
                            st.experimental_rerun()
                        except Exception:
                            st.session_state["_force_refresh"] = not st.session_state.get("_force_refresh", False)
            else:
                st.info("No files yet or failed to retrieve file list.")

        with col2:
            st.markdown("### Current User File List")
            if user_files_resp:
                if user_files_resp.get("files"):
                    for f in user_files_resp["files"]:
                        st.write(f)
                else:
                    st.info("This user currently has no files.")
            else:
                st.error("Failed to get this user's file list.")

        st.markdown("### Retrieval (RAG)")
        st.info("Mixed retrieval over personal + public KB (fill personal_k / public_k / final_k).")
        with st.form("retrieval_form_user"):
            question = st.text_input("Question", value="", key="q_user")
            personal_k = st.number_input("personal_k", min_value=0, value=5, step=1)
            public_k = st.number_input("public_k", min_value=0, value=5, step=1)
            final_k = st.number_input("final_k", min_value=0, value=5, step=1)
            threshold = st.text_input("threshold (optional, leave empty for None)", value="", help="If supported by backend, you can pass a float, e.g., 0.5")
            submitted = st.form_submit_button("Retrieve")
        if submitted:
            payload = {
                "question": question,
                "user_id": selected_user,
                "personal_k": personal_k,
                "public_k": public_k,
                "final_k": final_k,
            }
            if threshold.strip():
                try:
                    payload["threshold"] = float(threshold)
                except ValueError:
                    st.warning("Threshold is not a valid float; ignoring it.")
            if not question:
                st.error("Question cannot be empty.")
            else:
                with st.spinner("Retrieving..."):
                    retr = api_post_json("/retriever", payload)
                    if retr:
                        if retr.get("error"):
                            st.error(f"Retrieval error: {retr.get('message')}")
                        else:
                            st.success(f"Got {len(retr.get('hits', []))} hits")
                            st.subheader("Hits")
                            for i, hit in enumerate(retr.get("hits", [])):
                                st.markdown(f"**Hit {i+1}**")
                                st.json(hit)
                            img_path = retr.get("img_path")
                            if img_path:
                                st.markdown("**Returned image path / preview (if accessible)**")
                                st.write(img_path)
                                try:
                                    p = Path(img_path)
                                    if p.is_file():
                                        img_bytes = p.read_bytes()
                                        st.image(img_bytes, caption="retriever returned image (local)", use_container_width=True)
                                    else:
                                        # fallback to URL
                                        url = img_path if img_path.startswith("http") else f"{IMAGE_BASE.rstrip('/')}/{img_path.lstrip('/')}"
                                        st.image(url, caption="retriever returned image (http)", use_container_width=True)
                                except Exception:
                                    st.warning("Failed to load image from img_path.")
    else:
        st.warning("Please select a user_id.")

# -------- ADMIN MODE --------
else:
    st.subheader("Public Knowledge Base (Admin)")

    col1, col2 = st.columns([2, 5])
    with col1:
        st.markdown("### Upload Public File")
        uploaded_pub = st.file_uploader("Select a public file to upload", type=None, key="admin_upload", accept_multiple_files=False)
        if uploaded_pub:
            if st.button("Upload to public KB", key="upload_admin_btn"):
                with st.spinner("Uploading..."):
                    files = {"file": (uploaded_pub.name, uploaded_pub.getbuffer())}
                    resp = api_post_multipart("/admin/upload", files=files)
                    if resp and not resp.get("error"):
                        st.success(f"Upload succeeded: {uploaded_pub.name}")
                    else:
                        st.error(f"Upload failed: {resp}")
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    try:
                        st.experimental_rerun()
                    except Exception:
                        st.session_state["_force_refresh"] = not st.session_state.get("_force_refresh", False)

        st.markdown("---")
        st.markdown("### Delete Public Source")
        public_files_resp = api_get("/api/public_files")
        source_to_delete = None
        if public_files_resp and public_files_resp.get("files"):
            candidates = []
            for f in public_files_resp["files"]:
                candidates.append(f)
            source_to_delete = st.selectbox("Select public source_name to delete", candidates, key="del_pub_source")
            if st.button("Delete public source", key="del_pub_btn"):
                with st.spinner("Deleting..."):
                    data = {"source_name": source_to_delete}
                    resp = api_post_multipart("/admin/delete", data=data)
                    if resp and not resp.get("error"):
                        st.success(f"Deleted: {source_to_delete}")
                    else:
                        st.error(f"Deletion failed: {resp}")
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    try:
                        st.experimental_rerun()
                    except Exception:
                        st.session_state["_force_refresh"] = not st.session_state.get("_force_refresh", False)
        else:
            st.info("No public files available or failed to retrieve.")

    with col2:
        st.markdown("### Public File List")
        if public_files_resp:
            if public_files_resp.get("files"):
                for f in public_files_resp["files"]:
                    st.write(f)
            else:
                st.info("No public files.")
        else:
            st.error("Failed to retrieve public files.")

    st.markdown("### Retrieval (RAG)")
    st.info("You can combine personal and public knowledge bases for retrieval (to target a specific user, provide user_id).")
    with st.form("retrieval_form_admin"):
        question = st.text_input("Question", value="", key="q_admin")
        user_id = st.text_input("Optional user_id (leave empty to use only public)", value="")
        personal_k = st.number_input("personal_k", min_value=0, value=5, step=1)
        public_k = st.number_input("public_k", min_value=0, value=5, step=1)
        final_k = st.number_input("final_k", min_value=0, value=5, step=1)
        threshold = st.text_input("threshold (optional)", value="")
        submitted = st.form_submit_button("Retrieve")
    if submitted:
        payload = {
            "question": question,
            "user_id": user_id if user_id else None,
            "personal_k": personal_k,
            "public_k": public_k,
            "final_k": final_k,
        }
        if threshold.strip():
            try:
                payload["threshold"] = float(threshold)
            except ValueError:
                st.warning("Threshold is not a valid float; ignoring it.")
        if not question:
            st.error("Question cannot be empty.")
        else:
            with st.spinner("Retrieving..."):
                retr = api_post_json("/retriever", payload)
                if retr:
                    if retr.get("error"):
                        st.error(f"Retrieval error: {retr.get('message')}")
                    else:
                        st.success(f"Got {len(retr.get('hits', []))} hits")
                        st.subheader("Hits")
                        for i, hit in enumerate(retr.get("hits", [])):
                            st.markdown(f"**Hit {i+1}**")
                            st.json(hit)
                        img_path = retr.get("img_path")
                        if img_path:
                            st.markdown("**Returned image path / preview (if accessible)**")
                            st.write(img_path)
                            try:
                                url = img_path if img_path.startswith("http") else f"{IMAGE_BASE.rstrip('/')}/{img_path.lstrip('/')}"
                                st.image(url, caption="retriever returned image", use_container_width=True)
                            except Exception:
                                st.warning("Failed to load image from img_path.")
