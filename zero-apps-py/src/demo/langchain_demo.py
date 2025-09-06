import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.chains import RetrievalQA

# STEP 1: Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

# STEP 2: Load the document
loader = TextLoader("data.txt")  # Use a .txt or .pdf loader here
documents = loader.load()

# STEP 3: Split the text into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# STEP 4: Create embeddings
embeddings = OpenAIEmbeddings()

# STEP 5: Create a FAISS vector store
vectorstore = FAISS.from_documents(docs, embeddings)

# STEP 6: Create a RetrievalQA chain
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

# STEP 7: Ask questions
query = "What is the main topic of this document?"
result = qa_chain.invoke({"query": query})

# STEP 8: Display answer
print("Answer:", result["result"])
print("\nSources:")
for doc in result["source_documents"]:
    print("-", doc.metadata)
