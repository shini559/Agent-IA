import os
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import shutil
import gc
import time


class Rag:
    def __init__(self, docs_folder):
        load_dotenv(override=True)
        self.model = ChatOllama(model="llama3", temperature=0)
        self.embedder = OllamaEmbeddings(model="nomic-embed-text")

        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root
        project_root = os.path.dirname(script_dir)
        # Full path to docs folder
        self.folders_path = os.path.join(project_root, docs_folder)

        print(f"📂 Docs folder path: {self.folders_path}")

    def load_documents_from_folders(self, folders):
        all_chunks = []
        print(f"🔍 Scanning folders: {folders}")
        for folder in os.listdir(folders):
            if "db" in folder.split("_"):
                continue
            path_folder = os.path.join(folders, folder)
            if not os.path.isdir(path_folder):
                continue
            for file_name in os.listdir(path_folder):
                file_path = os.path.join(path_folder, file_name)
                if not os.path.isfile(file_path):
                    continue

                print(f"📄 Loading file: {file_path}")
                try:
                    # File type handling
                    if file_name.endswith(".xlsx"):
                        loader = UnstructuredExcelLoader(file_path)
                    elif file_name.endswith(".csv"):
                        loader = CSVLoader(file_path)
                    elif file_name.endswith(".pdf"):
                        loader = PyMuPDFLoader(file_path)
                    elif file_name.endswith(".txt") or file_name.endswith(".md"):
                        loader = TextLoader(file_path)
                    else:
                        print(f"⏩ Ignored unsupported file: {file_path}")
                        continue

                    loaded_document = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                    chunks = text_splitter.split_documents(loaded_document)

                    for chunk in chunks:
                        chunk.metadata["source"] = file_path
                        chunk.metadata["category"] = folder.split("/")[-1]

                    all_chunks.extend(chunks)

                except Exception as e:
                    print(f"❌ Error loading file {file_path}: {e}")
        return all_chunks

    def clear_vector_db(self, db_dir):
        # Force garbage collection to close files/connections
        gc.collect()
        # Retry deletion if locked, max 5 attempts
        for attempt in range(5):
            try:
                if os.path.exists(db_dir):
                    shutil.rmtree(db_dir)
                    print("🧹 Ancienne base vectorielle supprimée.")
                else:
                    print("Pas d'ancienne base vectorielle à supprimer.")
                return
            except PermissionError as e:
                print(f"⚠️ Tentative {attempt+1} - Impossible de supprimer la base vectorielle : {e}")
                print("  Attente avant nouvelle tentative...")
                time.sleep(1)
        print("❌ Échec de suppression de la base vectorielle, vérifier qu'aucun processus ne bloque le fichier.")

    def create_vector_db(self):
        db_dir = os.path.join(self.folders_path, "vector_db")

        print("🧹 Suppression de l'ancienne base vectorielle...")
        self.clear_vector_db(db_dir)

        # Chargement des documents
        all_loaded_chunks = self.load_documents_from_folders(self.folders_path)
        print("✅ Documents chargés.")
        print(f"📄 Nombre de chunks à indexer : {len(all_loaded_chunks)}")

        # Création de la base vectorielle
        try:
            vector_store = Chroma.from_documents(all_loaded_chunks, self.embedder, persist_directory=db_dir)
            db = Chroma(persist_directory=db_dir, embedding_function=self.embedder)
            print("✅ Base vectorielle créée avec succès.")
            return db
        except Exception as e:
            print(f"❌ Erreur lors de la création de la base vectorielle : {e}")
            return None

    def create_retriever(self):
        db = self.create_vector_db()
        if db is None:
            raise RuntimeError("Impossible de créer la base vectorielle, retriever non créé.")
        retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        self.retriever = retriever
        return retriever

    def chat_with_rag(self, user_input):
        if not hasattr(self, "retriever"):
            self.create_retriever()

        print("🔍 Recherche des documents pertinents...")
        relevant_chunks = self.retriever.invoke(user_input)
        print(f"📄 {len(relevant_chunks)} chunks retrouvés.")

        if not relevant_chunks:
            return "❗ Aucun document pertinent trouvé pour cette question."

        input_message = (
            f"Voici des documents à propos de l'emploi : \n\n"
            + "\n\n".join([chunk.page_content for chunk in relevant_chunks])
            + f"\n\nQuestion : {user_input}"
        )

        messages = [
            SystemMessage(content="Tu es un assistant qui aide à retrouver tout type d'informations lié à l'emploi et à l'insertion."),
            HumanMessage(content=input_message)
        ]

        print("🧠 Envoi au modèle...")
        try:
            result = self.model.invoke(messages)
            print("✅ Réponse générée.")
            return result.content
        except Exception as e:
            print(f"❌ Erreur lors de l'appel au modèle : {e}")
            return "Erreur lors de la génération de la réponse."


# --- Exécution de test ---
if __name__ == "__main__":
    rag = Rag("docs/")

    retriever = rag.create_retriever()
    print("📥 Retriever créé.")

    # Test affichage des documents pertinents
    docs = retriever.invoke("formation Hauts-de-France")
    for i, doc in enumerate(docs, 1):
        print(f"--- Document {i} ---\n{doc.page_content[:300]}...\n")

    # Test chat
    response = rag.chat_with_rag("Cite les organismes de formation en haut de france ?")
    print("🗣️ Réponse :", response)
