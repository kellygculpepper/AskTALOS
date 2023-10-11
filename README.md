AskTALOS
============

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

AskTALOS is a web app where users can talk to a chatbot that answers questions about the Evillious Chronicles and its lore. It uses Retrieval Augmented Generation (RAG) over articles scraped from the [Evillious Chronicles Wiki](https://theevilliouschronicles.fandom.com/wiki/The_Evillious_Chronicles_Wiki). The app is hosted [here](https://asktalos.streamlit.app/) (may be offline sometimes).

Usage
-----
To use the app locally, create a config.py file according to config_template.py, and run it with `streamlit run app.py`. This requires an OpenAI API key as well as a free Pinecone index for the embeddings.
