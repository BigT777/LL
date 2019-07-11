import psycopg2
import json
import nltk 
from string import punctuation
full_punctuation = punctuation + "–" + "," + "»" + "«" + "…" +'’'
from nltk.stem import WordNetLemmatizer 
lemmatizer = WordNetLemmatizer() 

from nltk.corpus import wordnet
DEBUG = False
BOTTOM_word_id = 0
UPPER_word_id = 100000#102401841
#conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')

def look_for_similar (word_id_offset, interval, debug = DEBUG):
    request = """SELECT word_id, word_lemma, jdesc->>'wd' AS ngram, word_rating FROM public.content_words
    WHERE (word_hash != 0) AND
    (((array_length(regexp_split_to_array(content_words.jdesc->>'wd', '[ ''-]'), 1) = 4) AND (content_words.word_rating >= 5)) OR
    ((array_length(regexp_split_to_array(content_words.jdesc->>'wd', '[ ''-]'), 1) = 3) AND (content_words.word_rating >= 5)) OR
    ((array_length(regexp_split_to_array(content_words.jdesc->>'wd', '[ ''-]'), 1) = 2) AND (content_words.word_rating >= 100)))
    AND (word_id >=""" + str(word_id_offset) + """)
    ORDER BY word_id ASC
    LIMIT """ + str(interval) 
    conn.rollback()
    cursor = conn.cursor()
    cursor.execute(request)
    for row in cursor:
        word_id = row[0]
        if row[1] == 0 or row[1] == None:
            print(row)
    return word_id

interval = 10
word_id = BOTTOM_word_id

while  word_id < UPPER_word_id and word_id != None:
    word_id = look_for_similar(word_id, interval)
    word_id += 1
    print(word_id)
conn.close()