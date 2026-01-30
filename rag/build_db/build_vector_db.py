from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

#parse pdf
def parse_file(pdf_pth,chunk_size=100,chunk_overlap=10):
  pdf_loader=PyPDFLoader(pdf_pth,extract_images=True)
  text_splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
  chunks=pdf_loader.load_and_split(text_splitter)
  return chunks

def load_embedding_models():
  embedding =  HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
  return embedding

def save_to_vector_db(chunks,embedding,db_pth):
  vector_db = FAISS.from_documents(chunks, embedding)
  vector_db.save_local(db_pth)
  print("saved!")

def load_vector_db(db_pth,embedding):
  vector_db = FAISS.load_local(db_pth, embedding)
  return vector_db
 