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
    page_icon = ':sun:',
    #layout = 'wide',
    menu_items = {
        # put the actual link
        'About': 'AskTALOS uses Retrieval Augmented Generation (RAG) over the [Evillious Chronicles Wiki](https://theevilliouschronicles.fandom.com/wiki/The_Evillious_Chronicles_Wiki). Source code & more info is available on [Github](https://github.com/)'
    }
)

'# AskTALOS'

# openai_api_key = st.sidebar.text_input('OpenAI API Key')
os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY
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

db = Pinecone.from_existing_index('ec', embedding = embeddings)
# adjust this? something to try to answer with as few docs as possible?
retriever = db.as_retriever(search_kwargs={'k': 5})

# model = ? gpt-3.5-turbo-16k or gpt-4??
chat_model = ChatOpenAI(temperature = 0)

compressor = LLMChainExtractor.from_llm(OpenAI(temperature = 0))
compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

tool = create_retriever_tool(
    compression_retriever,
    'search_evillious_docs',
    'Searches and returns documents about the Evillious Chronicles.'
)

tools = [tool]

memory = AgentTokenBufferMemory(memory_key='history', llm=chat_model)

system_message = SystemMessage(
    content = (
        "You are a helpful chatbot that answers questions about the Evillious Chronicles. "
        "The Evillious Chronicles is a Japanese multimedia dark fantasy series by mothy (a.k.a. Akuno-P). "
        "It includes Vocaloid songs, light novels, manga, and spin-offs. "
        "Unless otherwise specified, questions are probably about the Evillious Chronicles. "
        #"You are named after TALOS, a robot character from the series. If the user asks about TALOS, assume they mean the character unless you can infer they mean you. "
        # If the user mentions TALOS, you must infer whether they mean you or the character. If in doubt, assume they mean the character.
        "Feel free to use the tools provided to look up information as needed. "
        "If you cannot determine an answer using ONLY the information provided, just say you don't know. "
        # 'You are part of a web app called AskTALOS. The app was developed by Kelly Culpepper and has source code at [GITHUB]. All your information about the Evillious Chronicles is sourced from the fan wiki, https://theevilliouschronicles.fandom.com/wiki/The_Evillious_Chronicles_Wiki.'
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

if prompt := st.chat_input(placeholder=starter_message):
    st.chat_message('user').write(prompt)
    with st.chat_message('assistant'):
        #st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor(
            {'input': prompt, 'history': st.session_state.messages},
            include_run_info=True,
        )
        st.session_state.messages.append(AIMessage(content=response['output']))
        st.write(response['output'])
        memory.save_context({'input': prompt}, response)
        st.session_state['messages'] = memory.buffer
        run_id = response['__run'].run_id

