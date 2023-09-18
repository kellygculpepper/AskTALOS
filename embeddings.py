import config
import pinecone
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import Pinecone
import page_processor
import config

pinecone_index_name = config.PINECONE_INDEX_NAME

model_name = 'BAAI/bge-large-en-v1.5'
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}

embeddings = HuggingFaceBgeEmbeddings(
    model_name = model_name,
    model_kwargs = model_kwargs,
    encode_kwargs = encode_kwargs,
    query_instruction = "Represent this sentence for searching relevant passages:"
)

def create_db(links_file_path):
    """
    Given path to text file of links, creates Pinecone database "ec". 
    """
    with open(links_file_path) as f:
        links = f.read().splitlines()

    all_docs = []
    all_metadata = []

    for link in links:
        print(link)
        page_processor.add_page_data(link, all_docs, all_metadata)

    pinecone.init(
        api_key = config.PINECONE_API_KEY,
        environment = config.PINECONE_ENV
        )
    
    db = Pinecone.from_texts(all_docs, embedding = embeddings,
                               metadatas = all_metadata, index_name = pinecone_index_name)
    
    return db
    

db = create_db('data/links.txt')