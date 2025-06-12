from agents.agent import create_agent_executor

if __name__ == "__main__":
    print("🚀 Lancement de l'agent IA...")

    # Création de l'agent
    agent_executor = create_agent_executor()

    print("\n💬 Agent prêt ! Posez votre question :")

    # Boucle de chat simple
    while True:
        question = input("\n> ")

        if question.lower() in ['quit', 'exit', 'quitter']:
            print("Au revoir !")
            break

        if question.strip():
            response = agent_executor.invoke({"input": question})
            print(f"\n🤖 {response['output']}")