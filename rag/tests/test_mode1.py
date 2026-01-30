import os
import pytest
import shutil

# ------------ test user file upload mode 1 -------------- #
@pytest.mark.parametrize("user_id, filename", [
    ("U1", "doc_1.pdf"),
    ("U2", "doc_1.pdf")
])
def test_TEST_021_user_upload_mode1(mk_app_client, file_dir, user_id, filename, tmp_path):
    _, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir, filename)
    tmp_file = tmp_path / filename
    shutil.copyfile(file_path, tmp_file)

    with open(tmp_file, "rb") as f:
        r = client.post(
            "/user/upload",
            data={"user_id": user_id, "file": (f, filename)},
            content_type="multipart/form-data",
        )

    assert r.status_code == 200, r.get_json()
    j = r.get_json()
    assert j["admin"] is False
    assert j["chunk_collection"] == f"kb_user_{user_id}_chunk"
    assert j["user_id"] == user_id
    assert j["ingest_file"] == filename
    assert isinstance(j["chunk_embs_num"], int)
    assert j["page_collection"] == f"kb_user_{user_id}_page"
    assert isinstance(j["page_count"], int)
    assert isinstance(j["page_embs_num"], int)

    lst = client.get("/api/user_files", query_string={"user_id": user_id})
    assert lst.status_code == 200
    files_list = lst.get_json()["files"]
    assert filename in files_list


@pytest.mark.parametrize("user_id, filename", [
    ("U1", "doc_1.txt"),
    ("U1", "doc_1.docx")
])
def test_TEST_022_user_upload_pure_text_file_mode1(mk_app_client, file_dir, user_id, filename, tmp_path):
    _, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir, filename)
    tmp_file = tmp_path / filename
    shutil.copyfile(file_path, tmp_file)

    with open(tmp_file, "rb") as f:
        r = client.post(
            "/user/upload",
            data={"user_id": user_id, "file": (f, filename)},
            content_type="multipart/form-data",
        )

    assert r.status_code == 200, r.get_json()
    j = r.get_json()
    assert j["admin"] is False
    assert j["chunk_collection"] == f"kb_user_{user_id}_chunk"
    assert j["user_id"] == user_id
    assert j["ingest_file"] == filename
    assert isinstance(j["chunk_embs_num"], int)
    assert j["page_collection"] == f"kb_user_{user_id}_page"
    assert j["page_count"] is None
    assert j["page_embs_num"] is None

    lst = client.get("/api/user_files", query_string={"user_id": user_id})
    assert lst.status_code == 200
    files_list = lst.get_json()["files"]
    assert filename in files_list

# ------------ test user file delete mode 1 -------------- #
@pytest.mark.parametrize("user_id, filename", [
    ("U1", "doc_1.pdf"),
    ("U1", "doc_1.txt")
])
def test_TEST_023_user_delete_ok_mode1(mk_app_client, user_id,filename):
    _, client = mk_app_client(mode=1)

    r = client.post("/user/delete", data={"user_id": user_id, "source_name": filename})
    assert r.status_code == 200
    j = r.get_json()
    assert "deleted_page_embs" in j and "deleted_chunks" in j

    lst = client.get("/api/user_files", query_string={"user_id": user_id})
    assert r.status_code == 200
    assert filename not in lst.get_json().get("files", [])

# ------------ test admin file upload mode 1 -------------- #
@pytest.mark.parametrize("filename", [
    ("doc_1.pdf")
])
def test_TEST_024_admin_upload_ok_mode1(mk_app_client, filename,file_dir):
    _, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir,filename)
    with open(file_path, "rb") as f:
        r = client.post(
            "/admin/upload",
            data={"file": (f, filename)},
            content_type="multipart/form-data",
        )
    assert r.status_code == 200
    j = r.get_json()
    assert j["admin"] is True
    assert j["chunk_collection"] == "kb_admin_public_chunk"
    assert j["ingest_file"] == filename
    assert isinstance(j["chunk_embs_num"], int)
    assert j["page_collection"] == "kb_admin_public_page"
    assert isinstance(j["page_count"], int)
    assert isinstance(j["page_embs_num"], int)

    lst = client.get("/api/public_files")
    assert lst.status_code == 200
    assert filename in lst.get_json().get("files", [])

@pytest.mark.parametrize("filename", [
    ("doc_1.txt")
])
def test_TEST_025_admin_upload_pure_txt_ok_mode1(mk_app_client, filename,file_dir):
    _, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir,filename)
    with open(file_path, "rb") as f:
        r = client.post(
            "/admin/upload",
            data={"file": (f, filename)},
            content_type="multipart/form-data",
        )
    assert r.status_code == 200
    j = r.get_json()
    assert j["admin"] is True
    assert j["chunk_collection"] == "kb_admin_public_chunk"
    assert j["ingest_file"] == filename
    assert isinstance(j["chunk_embs_num"], int)
    assert j["page_collection"] == "kb_admin_public_page"
    assert j["page_count"] is None
    assert j["page_embs_num"] is None

    lst = client.get("/api/public_files")
    assert lst.status_code == 200
    assert filename in lst.get_json().get("files", [])

# ------------ test admin file delete mode 1 -------------- #
def test_TEST_026_admin_delete_ok_mode1(mk_app_client, file_dir):
    _, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir,"doc_1.pdf")
    with open(file_path, "rb") as f:
        client.post(
            "/admin/upload",
            data={"file": (f, "doc_1.pdf")},
            content_type="multipart/form-data",
        )

    r = client.post("/admin/delete", data={"source_name": "doc_1.pdf"})
    assert r.status_code == 200
    j = r.get_json()
    assert j["deleted_chunks"] > 0 and j["deleted_page_embs"] >0


@pytest.mark.parametrize("filename", [
    ("doc_1.pdf")
])
def test_TEST_027_multimodal_retrieve_ok_mode1(mk_app_client,file_dir,filename):
    app_mod, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir,filename)
    with open(file_path, "rb") as f:
        r = client.post(
            "/user/upload",
            data={"user_id": "User_Retriever", "file": (f, filename)},
            content_type="multipart/form-data",
        )
    assert r.status_code == 200

    payload = {
        "question": "Who is Han Meimei",
        "user_id": "User_Retriever",
        "personal_k": 30,
        "public_k": 30,
        "final_k": 5
    }
    resp = client.post("/multimodal_retriever", json=payload)
    assert resp.status_code == 200
    j = resp.get_json()
    assert "hits" in j
    assert isinstance(j["hits"], list)
    assert "img_path" in j

@pytest.mark.parametrize("payload", [
    {
        "user_id": "User_Retriever",
        "personal_k": 30,
        "public_k": 30,
        "final_k": 5
    },
    {
        "question": "Who is Han Meimei",
        "personal_k": 30,
        "public_k": 30,
        "final_k": 5
    },
    {
        "question": "Who is Han Meimei",
        "user_id": "User_Retriever",
        "public_k": 30,
        "final_k": 5
    }, 
    {
        "question": "Who is Han Meimei",
        "user_id": "User_Retriever",
        "personal_k": 30,
        "final_k": 5
    },       
    {},
])         
def test_TEST_028_multimodal_retrieve_missing_params_mode1(mk_app_client,payload):
    _, client = mk_app_client(mode=1)

    r = client.post("/multimodal_retriever", json=payload)
    assert r.status_code == 400
    j = r.get_json()
    assert j["error"] is True
    assert "personal_k" in j["message"] or "Request must include" in j["message"]

@pytest.mark.parametrize("filename", [
    ("doc_1.pdf")
])
def test_TEST_029_multimodal_retrieve_internal_error_mode1(mk_app_client, monkeypatch, file_dir, filename):
    _, client = mk_app_client(mode=1)
    file_path = os.path.join(file_dir, filename)
    with open(file_path, "rb") as f:
        client.post(
            "/user/upload",
            data={"user_id": "User_MM_Error", "file": (f, filename)},
            content_type="multipart/form-data",
        )

    from rag import app as app_module
    monkeypatch.setattr(
        app_module.CompositeRetriever,
        "cascade_retrieve",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom_mm"))
    )

    payload = {
        "question": "Who is Han Meimei",
        "user_id": "User_MM_Error",
        "personal_k": 30,
        "public_k": 30,
        "final_k": 5
    }
    r = client.post("/multimodal_retriever", json=payload)
    assert r.status_code == 500
    j = r.get_json()
    assert j["error"] is True
    assert "boom_mm" in j["detail"]