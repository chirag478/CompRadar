"""
Vercel Python Serverless Entrypoint for CompRadar
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import database
from server import ScraperHandler

database.init_db()

class handler(ScraperHandler):
    pass
