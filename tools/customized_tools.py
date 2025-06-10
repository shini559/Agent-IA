from langchain.agents import Tool
from langchain.tools import tool
from duckduckgo_search import DDGS
from utils.rag import Rag



 
from langchain.agents import Tool

def search_docs(query: str, rag_instance: Rag) -> str:
    retriever = rag_instance.get_retriever()
    docs = retriever.invoke(query)
    return "\n".join([doc.page_content for doc in docs])

# Create a Tool instance
def get_search_docs_tool(rag_instance: Rag) -> Tool:
    return Tool(
        name="search_docs",
        func=lambda q: search_docs(q, rag_instance),
        description="Useful for searching relevant documents in the vector database."
    )

    


def search_web(query: str, max_results: int = 3) -> str:
    """
    Recherche une information sur le web via DuckDuckGo.

    Args:
        query (str): La question ou sujet à rechercher.
        max_results (int): Nombre de résultats à retourner.

    Returns:
        str: Résumé des résultats trouvés.
    """
    if not query.strip():
        return "Veuillez fournir une requête valide."

    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']} - {r['href']}\n{r['body']}\n")

        return "\n".join(output) if output else "Aucun résultat trouvé."
    

# Déclaration du Tool à partir de la fonction directement
# Create a Tool instance
def get_search_web_tool() -> Tool:
    return Tool(
    name="search_web",
    func=lambda q: search_web(q),
    description="Recherche des informations actuelles sur Internet via DuckDuckGo."
)

if __name__ == "__main__":
    print(search_web("dernières nouvelles sur l'emploi et insertion"))