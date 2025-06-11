import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from langchain import hub
from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from tools.tools import tools


def create_agent_executor():
    """
    Crée et renvoie un exécuteur d'agent prêt à l'emploi,
    MAINTENANT AVEC UNE MÉMOIRE.
    """
    print("Création de l'agent avec mémoire...")

    # 1. On récupère le prompt depuis le Hub
    prompt = hub.pull("hwchase17/react-chat")

    # 2. On choisit le modèle de langage
    llm = ChatOllama(model="llama3", temperature=0)

    # On configure la mémoire de l'agent.
    memory = ConversationBufferMemory(memory_key="chat_history")

    # 3. On crée l'agent en lui donnant le llm, les outils et le prompt
    agent = create_react_agent(llm, tools, prompt)

    # 4. On crée l'exécuteur d'agent.
    # NOUVEAU : On ajoute le paramètre `memory` ici !
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,  # L'ajout crucial est ici
        verbose=True
    )

    print("Agent avec mémoire prêt !")
    return agent_executor
