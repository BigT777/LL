import psycopg2
import json
from tqdm import tqdm
import statistics
import multiprocessing 
import time
import random

conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
cursor = conn.cursor()