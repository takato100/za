import os
from pathlib import Path

# TODO: Set these in ~/.zshrc on MacBook
# export SCRAPBOX_PROJECT="your-project-name"
# export SCRAPBOX_CONNECT_SID="your-connect-sid-cookie"
SCRAPBOX_PROJECT = os.getenv("SCRAPBOX_PROJECT", "TODO_SET_SCRAPBOX_PROJECT")
SCRAPBOX_CONNECT_SID = os.getenv("SCRAPBOX_CONNECT_SID", "TODO_SET_CONNECT_SID")

INDEX_DIR = Path.home() / ".scrapbox_mcp"
INDEX_DIR.mkdir(exist_ok=True)

# Multilingual model, handles Japanese well (~120MB)
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
