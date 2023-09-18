import config
import os
import streamlit as st
from langchain.llms import OpenAI
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent, create_retriever_tool
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever
from langchain.schema import SystemMessage, AIMessage, HumanMessage

st.set_page_config(
    page_title = 'AskTALOS',
    page_icon = '☀️',
    #layout = 'wide',
    menu_items = {
        'Report a bug': 'https://github.com/kellygculpepper/AskTALOS/issues',
        'About': '''# About AskTALOS
        AskTALOS uses Retrieval Augmented Generation (RAG) over the [Evillious Chronicles Wiki](https://theevilliouschronicles.fandom.com/wiki/The_Evillious_Chronicles_Wiki). Source code & more info is available on [Github](https://github.com/kellygculpepper/AskTALOS).
        '''
    }
)

'# AskTALOS'

# openai_api_key = st.sidebar.text_input('OpenAI API Key')
os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY
pinecone_index_name = config.PINECONE_INDEX_NAME
pinecone.init(
    api_key = config.PINECONE_API_KEY,
    environment = config.PINECONE_ENV
)

embeddings = HuggingFaceBgeEmbeddings(
    model_name = 'BAAI/bge-large-en-v1.5',
    model_kwargs = {'device': 'cpu'},
    encode_kwargs = {'normalize_embeddings': True},
    query_instruction = 'Represent this sentence for searching relevant passages:'
)

db = Pinecone.from_existing_index(pinecone_index_name, embedding = embeddings)
# adjust this?
retriever = db.as_retriever(search_kwargs={'k': 6})

# model = ? gpt-3.5-turbo-16k or gpt-4??
chat_model = ChatOpenAI(model_name = 'gpt-4', temperature = 0)

compressor = LLMChainExtractor.from_llm(ChatOpenAI(model_name = 'gpt-4', temperature = 0))
compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

tool = create_retriever_tool(
    compression_retriever,
    'search_evillious_articles',
    'Searches and returns sections of Wiki articles about the Evillious Chronicles.'
)

tools = [tool]

memory = AgentTokenBufferMemory(memory_key='history', llm=chat_model)

system_message = SystemMessage(
    content = (
        "You are a helpful chatbot that answers questions about the Evillious Chronicles, a Japanese multimedia dark fantasy series by mothy (aka Akuno-P). "
        "Feel free to use the tools provided to look up information as needed. Use this information as context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
    )
)

# might need to change token limit
agent_executor = create_conversational_retrieval_agent(chat_model, tools = tools, verbose = True, system_message = system_message, memory_key = 'history', remember_intermediate_steps = True, max_token_limit = 4000)

starter_message = 'Hello! Ask me anything about the Evillious Chronicles.'

if 'messages' not in st.session_state:
    st.session_state['messages'] = [AIMessage(content=starter_message)]

for msg in st.session_state.messages:
    if isinstance(msg, AIMessage):
        st.chat_message('assistant', avatar = '🦇').write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message('user', avatar = '👤').write(msg.content)
    memory.chat_memory.add_message(msg)

if prompt := st.chat_input(placeholder= 'Send a message'):
    st.chat_message('user', avatar = '👤').write(prompt)
    with st.chat_message('assistant', avatar = '🦇'):
        response = agent_executor(
            {'input': prompt, 'history': st.session_state.messages},
            include_run_info=True,
        )
        st.session_state.messages.append(AIMessage(content=response['output']))
        st.write(response['output'])
        memory.save_context({'input': prompt}, response)
        st.session_state['messages'] = memory.buffer
        run_id = response['__run'].run_id

