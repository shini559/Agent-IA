
from utils.rag import Rag
from langchain.tools.retriever import create_retriever_tool

# On crée les retrievers en appelant notre fonction
retriever_emploi = Rag("docs\\emploi\\")
retriever_formation = Rag("docs\\formation")
retriever_salaire = Rag("docs\\salaire\\")

# --- Création des Outils ---
# C'est ici que la magie opère. Chaque outil a une description claire
# que l'agent utilisera pour faire son choix.

# Outil pour la recherche sur l'emploi
tool_emploi = create_retriever_tool(
    retriever_emploi,
    "recherche_aide_emploi",
    "Très utile pour trouver des informations sur les aides à l'emploi, les formations, et les dispositifs d'insertion professionnelle."
)

# Outil pour la recherche sur les formations
tool_formation = create_retriever_tool(
    retriever_formation,
    "recherche_formation",
    "Permet de rechercher des informations sur les formations, les aides à la formation, et les dispositifs d'accompagnement à l'emploi."
)

# Outil pour la recherche sur le salaire
tool_salaire = create_retriever_tool(
    retriever_salaire,
    "recherche_salaire",
    "Utile pour trouver des informations sur les salaires, les grilles salariales, et les aides financières liées à l'emploi."
)

# On rassemble tous nos outils RAG
rag_tools = [tool_emploi, tool_formation, tool_salaire]
