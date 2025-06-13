import os
import shutil
import time
from typing import List, Optional
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.retrievers import BaseRetriever


class Rag:
    def __init__(self, docs_folder: str):
        print("docs folder", docs_folder)
        """Initialise le système RAG avec le dossier de documents."""
        load_dotenv(override=True)

        # Configuration des modèles
        self.model = ChatDeepSeek(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0.3  # Un peu de créativité
        )
        self.embedder = OllamaEmbeddings(model="nomic-embed-text")

        # Chemins des fichiers
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        self.docs_path = os.path.join(project_root, docs_folder)
        self.db_dir = os.path.join(self.docs_path, "vector_db")

        # Initialisation de la base vectorielle
        self._initialize_vector_db()

    def _initialize_vector_db(self) -> None:
        """Initialise ou charge la base vectorielle."""
        if not os.path.exists(self.db_dir):
            print("🛠️ Création de la base vectorielle...")
            self._create_vector_db()
        else:
            print("🔍 Chargement de la base existante...")
            self.vector_store = Chroma(
                persist_directory=self.db_dir,
                embedding_function=self.embedder
            )

    def _load_single_document(self, file_path: str, category: str) -> List[Document]:
        """Charge un seul document avec le loader approprié."""
        print("load single doc",file_path, "category", category )
        try:
            if file_path.endswith(".xlsx"):
                loader = UnstructuredExcelLoader(file_path)
            elif file_path.endswith(".csv"):
                loader = CSVLoader(file_path)
            elif file_path.endswith(".pdf"):
                loader = PyMuPDFLoader(file_path)
            elif file_path.endswith((".txt", ".md")):
                loader = TextLoader(file_path)
            else:
                return []

            docs = loader.load()
            for doc in docs:
                doc.metadata.update({
                    "source": os.path.basename(file_path),
                    "category": category
                })
            return docs

        except Exception as e:
            print(f"⚠️ Erreur sur {file_path}: {str(e)}")
            return []

    def load_documents(self) -> List[Document]:
        """Charge tous les documents depuis le dossier configuré."""
        all_docs = []

        for category in os.listdir(self.docs_path):
            print("category", category)
            if category.startswith(".") or "db" in category.lower():
                continue

            category_path = os.path.join(self.docs_path, category)
            if not os.path.isdir(category_path):
                continue

            for file_name in os.listdir(category_path):
                file_path = os.path.join(category_path, file_name)
                if os.path.isfile(file_path):
                    all_docs.extend(self._load_single_document(file_path, category))

        return all_docs
    
    def load_documents_from_folder(self) -> List[Document]:
        """Charge tous les documents depuis un dossier plat (sans sous-dossiers)."""
        all_docs = []
        print("load docs from folder")
        for file_name in os.listdir(self.docs_path):
            file_path = os.path.join(self.docs_path, file_name)
            if os.path.isfile(file_path):
            # Utilise une catégorie par défaut ou extraite du nom du fichier si besoin
                print("self.docs_folder", self.docs_path)
                
                category = file_path.split("/")[-2]
                all_docs.extend(self._load_single_document(file_path, category))

        return all_docs


    def _create_vector_db(self) -> None:
        """Crée une nouvelle base vectorielle."""
        # Nettoyage préalable
        self._clean_vector_db()

        # Chargement et découpage des documents
        docs = self.load_documents()
        if not docs:
            raise ValueError("Aucun document valide trouvé")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=0,  # Important pour le contexte
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(docs)

        # Création de la base
        
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedder,
            persist_directory=self.db_dir,
            collection_metadata={"hnsw:space": "cosine"}  # Optimisation
        )
        print(f"✅ Base créée avec {len(chunks)} chunks")
        

    def _clean_vector_db(self, max_attempts: int = 3) -> None:
        """Nettoie le répertoire de la base vectorielle."""
        for attempt in range(max_attempts):
            try:
                if os.path.exists(self.db_dir):
                    shutil.rmtree(self.db_dir)
                    print("🧹 Ancienne base supprimée")
                    time.sleep(1)  # Pause pour le système de fichiers
                return
            except Exception as e:
                print(f"⚠️ Tentative {attempt + 1}: {str(e)}")
                time.sleep(2)
        raise RuntimeError("Impossible de nettoyer le répertoire")

    def get_retriever(self, k: int = 3) -> BaseRetriever:
        """Retourne un retriever configuré."""
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    def query(self, question: str, k: int = 3) -> str:
        """Exécute une requête RAG complète."""
        retriever = self.get_retriever(k)

        # Récupération des documents pertinents
        docs = retriever.invoke(question)
        if not docs:
            return "Aucune information pertinente trouvée."

        # Construction du contexte
        context = "\n\n---\n\n".join(
            f"Source: {doc.metadata['source']}\nContenu: {doc.page_content}"
            for doc in docs
        )

        # Génération de la réponse
        response = self.model.invoke([
            SystemMessage(content="""Tu es un expert en emploi et formation.
Réponds de manière précise en t'appuyant sur les documents fournis."""),
            HumanMessage(content=f"""Contexte:
{context}

Question: {question}""")
        ])

        # Ajout des sources
        sources = ", ".join(set(doc.metadata["source"] for doc in docs))
        return f"{response.content}\n\nSources: {sources}"


if __name__ == "__main__":
    try:
        rag = Rag("docs/")
        """
        while True:
            question = input("\n💬 Posez votre question (ou 'quit'): ").strip()
            if question.lower() in ('quit', 'exit', 'q'):
                break

            start_time = time.time()
            response = rag.query(question)
            print(f"\n🤖 Réponse ({time.time() - start_time:.2f}s):\n{response}")
        """
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")