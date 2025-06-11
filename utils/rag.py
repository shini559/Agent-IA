
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings


# Cette fonction évite de répéter le même code pour chaque catégorie.
def create_rag_retriever(folder_path: str):
    """Crée un retriever RAG à partir des documents d'un dossier."""
    # Vérifie si le dossier existe
    if not os.path.isdir(folder_path):
        # Retourne un "retriever vide" si le dossier n'existe pas pour éviter les erreurs
        return Chroma.from_texts(["pas de documents"], OllamaEmbeddings(model="nomic-embed-text")).as_retriever()

    def csv_loader(file_path: str):
        return TextLoader(file_path, encoding="utf-8")

    try:
        loader = DirectoryLoader(
            folder_path,
            glob="**/*.{txt,csv,md}",
            recursive=True,
            show_progress=True,
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        docs = loader.load()
    except Exception as e:
        print(f"Erreur lors du chargement des documents: {e}")
        # En cas d'erreur, on essaie sans paramètres spécifiques
        loader = DirectoryLoader(
            folder_path,
            glob="**/*.{txt,csv,md}",
            recursive=True,
            show_progress=True
        )
        docs = loader.load()

    # Si le dossier est vide, on gère le cas
    if not docs:
        return Chroma.from_texts(["pas de documents"], OllamaEmbeddings(model="nomic-embed-text")).as_retriever()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    vectorstore = Chroma.from_documents(documents=splits, embedding=OllamaEmbeddings(model="nomic-embed-text"))

    return vectorstore.as_retriever()