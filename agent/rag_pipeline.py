import os
import sqlite3
import json
from datetime import datetime
import chromadb
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class RAGPipeline:
    def __init__(
        self,
        chroma_path="./chroma_db",
        collection_name="construction_procedures",
        sqlite_path="qa_log.db",
        top_k=5,
        similarity_threshold=0.50,
    ):

        # Connect to ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_collection(collection_name)

        # Connect to Claude
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Load system prompt
        with open("agent/system_prompt.txt", "r") as f:
            self.system_prompt_template = f.read()

        # Settings
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.sqlite_path = sqlite_path

        # Set up SQLite logging
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                question TEXT,
                retrieved_chunks TEXT,
                response TEXT,
                answered INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def retrieve(self, query):
        """Search ChromaDB for the most relevant chunks."""
        results = self.collection.query(query_texts=[query], n_results=self.top_k)

        chunks = []
        sources = []

        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                similarity = 1 - distance

                if similarity >= self.similarity_threshold:
                    chunks.append(doc)
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    source = meta.get("source_file", "unknown")
                    page = meta.get("page", "")
                    sources.append(f"{source} (page {page})")

        return chunks, sources

    def ask(self, question):
        """Run the full RAG pipeline for a question."""
        # Step 1: Retrieve relevant chunks
        chunks, sources = self.retrieve(question)

        # Step 2: Check if we have enough context
        answered = True
        if not chunks:
            answered = False
            context = "No relevant context found."
        else:
            context = "\n\n---\n\n".join(chunks)

        # Step 3: Build the prompt
        prompt = self.system_prompt_template.replace("{context}", context).replace(
            "{question}", question
        )

        # Step 4: Call Claude API
        message = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        response = message.content[0].text

        # Step 5: Check if agent flagged as unanswered
        if "I cannot find this information" in response:
            answered = False
            self._log_unanswered(question)

        # Step 6: Log to SQLite
        self._log_to_db(question, chunks, response, answered)

        return {
            "question": question,
            "response": response,
            "sources": sources,
            "answered": answered,
        }

    def _log_to_db(self, question, chunks, response, answered):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute(
            """
            INSERT INTO qa_log (timestamp, question, retrieved_chunks, response, answered)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                question,
                json.dumps(chunks),
                response,
                int(answered),
            ),
        )
        conn.commit()
        conn.close()

    def _log_unanswered(self, question):
        """Append unanswered question to CSV for gap repository."""
        import csv

        filepath = "evaluation/unanswered_questions.csv"
        file_exists = os.path.exists(filepath)
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "question"])
            writer.writerow([datetime.now().isoformat(), question])


# Quick test when run directly
if __name__ == "__main__":
    pipeline = RAGPipeline()
    test_questions = [
        "At what height is fall protection required?",
        "What are the water requirements for heat illness prevention?",
        "What is the recipe for chocolate cake?",
    ]
    for q in test_questions:
        print(f"\nQ: {q}")
        result = pipeline.ask(q)
        print(f"A: {result['response'][:300]}")
        print(f"Sources: {result['sources']}")
        print(f"Answered: {result['answered']}")
