# -*- coding: utf-8 -*-


from vilt.keywordsmanager import KeywordsManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
prompt = """El método de los k vecinos más cercanos (en inglés: k-nearest neighbors, abreviado k-nn) es un método de
 clasificación supervisada (Aprendizaje, estimación basada en un conjunto de formación y prototipos) que sirve 
 para estimar la función de densidad de las predictoras por cada clase."""
keyword_manager = KeywordsManager()
result = keyword_manager.generate_keywords(prompt)
print(result)
