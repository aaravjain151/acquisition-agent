from dotenv import load_dotenv
load_dotenv()

from graph import graph

if __name__ == "__main__":
    target = "Air conditioning repair services in Los Angeles, CA"
    config = {"configurable": {"thread_id": "demo-1"}}
    result = graph.invoke({"target": target}, config)

    print("\n=== SCOPE (real LLM output) ===\n")
    print(result["scope"])
    print("\n=== REPORT (stub) ===\n")
    print(result["report"])
