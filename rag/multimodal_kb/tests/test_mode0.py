import os
import pytest
import shutil
from ..data_parser import get_chunks_from_pdf

# ------------ test user file upload mode 0 -------------- #
@pytest.mark.parametrize("user_id, filename", [
    ("U1", "doc_1.pdf"),
    ("U2", "doc_1.pdf"),
    ("U1", "doc_1.docx"),
    ("U1", "doc_1.txt")
])
def test_TEST_001_user_upload_mode0(mk_app_client,file_dir, user_id, filename, tmp_path):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,filename)
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
    assert j["page_collection"] == ""
    assert j["page_count"] is None
    assert j["page_embs_num"] is None

    lst = client.get("/api/user_files", query_string={"user_id": user_id})
    print(lst.get_json()["files"])
    assert lst.status_code == 200
    assert filename in lst.get_json()["files"]

def test_TEST_002_upload_missing_user_id(mk_app_client, file_dir):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,"doc_1.pdf")
    with open(file_path, "rb") as f:
        r = client.post("/user/upload",
                        data={"file": (f, "doc_1.pdf")},
                        content_type="multipart/form-data")
    assert r.status_code == 400

def test_TEST_003_upload_missing_file(mk_app_client, file_dir):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,"doc_1.pdf")
    with open(file_path, "rb") as f:
        r = client.post("/user/upload",
                        data={"user_id": "U1"},
                        content_type="multipart/form-data")
    assert r.status_code == 400

# ------------ test user file delete mode 0 -------------- #
@pytest.mark.parametrize("user_id, filename", [
    ("U1", "doc_1.pdf")
])
def test_TEST_004_user_delete_ok_mode0(mk_app_client, user_id,filename):
    _, client = mk_app_client(mode=0)

    r = client.post("/user/delete", data={"user_id": user_id, "source_name": filename})
    assert r.status_code == 200
    j = r.get_json()
    assert "deleted_page_embs" in j and "deleted_chunks" in j

    lst = client.get("/api/user_files", query_string={"user_id": user_id})
    assert r.status_code == 200
    assert filename not in lst.get_json().get("files", [])

@pytest.mark.parametrize("payload", [
    {"user_id": "U1"},         # missing source_name
    {"source_name": "doc_1.pdf"},        #missing user_id
    {},                                 # missing both
])
def test_TEST_005_user_delete_missing_params_mode0(mk_app_client, payload):
    _, client = mk_app_client(mode=0)
    r = client.post("/user/delete", data=payload)
    assert r.status_code == 400
    j = r.get_json()
    assert j["error"] is True
    assert "user_id" in j["message"] and "source_name" in j["message"]

def test_TEST_006_user_delete_nonexistent_mode0(mk_app_client):
    _, client = mk_app_client(mode=0)
    r = client.post("/user/delete", data={"user_id": "U1", "source_name": "doc_1.pdf"})
    assert r.status_code == 200
    j = r.get_json()
    assert j["deleted_chunks"] ==0 and j["deleted_page_embs"] == 0

def test_TEST_007_user_delete_other_users_file_mode0(mk_app_client, file_dir):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,"doc_1.pdf")
    with open(file_path, "rb") as f:
        client.post(
            "/user/upload",
            data={"user_id": "OWNER", "file": (f, "owner.pdf")},
            content_type="multipart/form-data",
        )

    r = client.post("/user/delete", data={"user_id": "ATTACKER", "source_name": "owner.pdf"})
    assert r.status_code == 200
    # OWNER still exist
    lst = client.get("/api/user_files", query_string={"user_id": "OWNER"})
    assert "owner.pdf" in lst.get_json().get("files", [])

# ------------ test admin file upload mode 0 -------------- #
@pytest.mark.parametrize("filename", [
    ("doc_1.pdf"),
    ("doc_1.docx"),
    ("doc_1.txt")
])
def test_TEST_008_admin_upload_ok_mode0(mk_app_client, filename,file_dir):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,filename)
    chunk_embs_num = len(get_chunks_from_pdf(file_path))
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
    assert j["chunk_embs_num"] ==  chunk_embs_num# chunk embeddings number of this file
    assert j["page_collection"] == ""
    assert j["page_count"] is None
    assert j["page_embs_num"] is None

    lst = client.get("/api/public_files")
    assert lst.status_code == 200
    assert filename in lst.get_json().get("files", [])

def test_TEST_009_admin_upload_missing_file_mode0(mk_app_client):
    _, client = mk_app_client(mode=0)
    r = client.post("/admin/upload", data={}, content_type="multipart/form-data")
    assert r.status_code == 400
    j = r.get_json()
    assert j["error"] is True and "file" in j["message"]

@pytest.mark.parametrize("filename", [
    ("doc_empty.pdf")
])
def test_TEST_010_admin_upload_empty_file_mode0(mk_app_client, filename,file_dir):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,filename)
    chunk_embs_num = len(get_chunks_from_pdf(file_path))
    with open(file_path, "rb") as f:
        r = client.post(
            "/admin/upload",
            data={"file": (f, filename)},
            content_type="multipart/form-data",
        )
    assert r.status_code == 200

    lst = client.get("/api/public_files")
    assert lst.status_code == 200
    assert filename not in lst.get_json().get("files", [])

# ------------ test admin file delete mode 0 -------------- #
def test_TEST_011_admin_delete_ok_mode0(mk_app_client, file_dir):
    _, client = mk_app_client(mode=0)
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
    assert j["deleted_chunks"] >= 0

def test_TEST_012_admin_delete_missing_params_mode0(mk_app_client):
    _, client = mk_app_client(mode=0)
    r = client.post("/admin/delete", data={})
    assert r.status_code == 400
    j = r.get_json()
    assert j["error"] is True
    assert "source_name" in j["message"]

def test_TEST_013_admin_delete_nonexistent_mode0(mk_app_client):
    _, client = mk_app_client(mode=0)
    r = client.post("/admin/delete", data={"source_name": "doc_1.pdf"})
    assert r.status_code == 200
    j = r.get_json()
    assert j["deleted_chunks"] ==0 and j["deleted_page_embs"] == 0

# ------------ test retrieve mode 0 -------------- #
@pytest.mark.parametrize("filename", [
    ("doc_1.pdf")
])
def test_TEST_014_retrieve_ok_mode0(mk_app_client,file_dir,filename):
    app_mod, client = mk_app_client(mode=0)
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
    resp = client.post("/retriever", json=payload)
    assert resp.status_code == 200
    j = resp.get_json()
    assert "hits" in j
    assert isinstance(j["hits"], list)

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
def test_TEST_015_etrieve_missing_params_mode0(mk_app_client,payload):
    _, client = mk_app_client(mode=0)

    r = client.post("/retriever", json=payload)
    assert r.status_code == 400
    j = r.get_json()
    assert j["error"] is True
    assert "personal_k" in j["message"] or "Request must include" in j["message"]

@pytest.mark.parametrize("filename", [
    ("doc_1.pdf")
])
def test_TEST_016_retrieve_internal_error_mode0(mk_app_client, monkeypatch,file_dir,filename):
    _, client = mk_app_client(mode=0)
    file_path = os.path.join(file_dir,filename)
    with open(file_path, "rb") as f:
        client.post(
            "/user/upload",
            data={"user_id": "User_Error", "file": (f, filename)},
            content_type="multipart/form-data",
        )

    from rag.multimodal_kb import app as app_module
    monkeypatch.setattr(
        app_module.CompositeRetriever,
        "chunk_retrieve_with_reranker",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    payload = {
        "question": "Who is Han Meimei",
        "user_id": "User_Error",
        "personal_k": 30,
        "public_k": 30,
        "final_k": 5
    }
    r = client.post("/retriever", json=payload)
    assert r.status_code == 500
    j = r.get_json()
    assert j["error"] is True
    assert "boom" in j["detail"]

# ------------ test get users -------------- #
def test_TEST_017_get_users_ok(mk_app_client):
    _, client = mk_app_client()
    r = client.get("/api/users")
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j, dict)
    assert "users" in j                       # 必须有 users 字段
    assert isinstance(j["users"], list)       # users 必须是 list

def test_TEST_018_get_user_files_missing_user_id(mk_app_client):
    _, client = mk_app_client()
    r = client.get("/api/user_files")  # 不传 user_id
    assert r.status_code == 400
    j = r.get_json()
    assert isinstance(j, dict)
    assert j["error"] is True

# ------------ test get user files -------------- #
def test_TEST_019_get_user_files_ok(mk_app_client):
    _, client = mk_app_client()
    r = client.get("/api/user_files", query_string={"user_id": "U1"})
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j, dict)
    assert "files" in j
    assert isinstance(j["files"], list)

# ------------ test get public files -------------- #
def test_TEST_020_get_public_files_ok(mk_app_client):
    _, client = mk_app_client()
    r = client.get("/api/public_files")
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j, dict)
    assert "files" in j
    assert isinstance(j["files"], list)

