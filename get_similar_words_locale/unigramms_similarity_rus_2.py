import psycopg2
import json
from tqdm import tqdm
import statistics
import random
from Levenshtein import distance
import multiprocessing 
import time
import random
import pymorphy2
import re

START_WORD_ID = 150000
FIN_WORD_ID =  250000#5000001000000 10000000 50000000 102401840
DEBUG = False

#conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')
conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')

morph = pymorphy2.MorphAnalyzer()
cursor = conn.cursor()
with open("unigram_pos_lemma_rus.json","r") as f:
    letter_count_dict = json.load(f)

def write_response (json_file, start_index, final_index):
    file_name = './save_unigr_rus_2/' + str(start_index) + '-' + str(final_index) +'.json'
    print("\nNOW SAVING", file_name,'\n')
    with open(file_name, 'w', encoding = "utf-8") as outfile:
        json.dump(json_file, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)
    
def iterate_insde_dict(collected_words_list, word, lemma, pos,examined_word_len, letter_count_dict, search_range, debug = DEBUG):
    collected_words = 0
    #print(word, examined_word_len, "search_range", search_range)
    if str(examined_word_len) in letter_count_dict and examined_word_len > 2:
        compare_words = letter_count_dict[str(examined_word_len)]
        random.shuffle(compare_words)
        for word_compare_el in compare_words:
            word_compare = word_compare_el[0]
            pos_compare = word_compare_el[1]
            lemm_comapre = word_compare_el[2]
            if search_range > 3:
                pos_search_range = search_range
            else:
                pos_search_range = 1
            
            if pos and pos_compare:
                if distance(lemm_comapre, lemma) > 0 and distance(lemm_comapre, lemma)  <= search_range and distance(pos_compare, pos) <= pos_search_range:
                    if debug:print("FOUND VS POS", word,word_compare,lemma, lemm_comapre, pos,pos_compare)
                    collected_words_list.append(word_compare)
                    collected_words += 1
                    if (collected_words > 10 or len(collected_words_list) > 20):break
            else:
                if distance(lemm_comapre, lemma) > 0 and distance(lemm_comapre, lemma)  <= search_range:
                    if debug:print("FOUND NON POS", word,word_compare,lemma, lemm_comapre)
                    collected_words_list.append(word_compare)
                    collected_words += 1
                    if (collected_words > 10 or len(collected_words_list) > 20):break
    #print("collected_words_list",collected_words_list)
    return collected_words

def look_inside_dict(word, lemma, pos, collected_words_list, word_len, search_range,debug = DEBUG):
    if debug:print (word, "word_len", word_len, "search range", search_range)
    total_words = len(collected_words_list)
    if search_range > 7:
        word_len = 6
    if(word_len > 2):
        new_words_collected_count = iterate_insde_dict(collected_words_list, word, lemma, pos,word_len-1, letter_count_dict, search_range)
        total_words += new_words_collected_count
        new_words_collected_count = iterate_insde_dict(collected_words_list, word, lemma, pos,word_len, letter_count_dict, search_range)
        total_words += new_words_collected_count
    new_words_collected_count = iterate_insde_dict(collected_words_list, word, lemma, pos,word_len+1, letter_count_dict, search_range)
    total_words += new_words_collected_count
    if(word_len <= 2):
        new_words_collected_count = iterate_insde_dict(collected_words_list, word, lemma, pos,word_len+2, letter_count_dict, search_range)
        total_words += new_words_collected_count
    while total_words < 20:
        search_range += 1
        look_inside_dict(word, lemma, pos, collected_words_list, word_len, search_range)
        total_words = len(list(set(collected_words_list)))
        if debug:print("len_after_recursion", len(list(set(collected_words_list))))
    collected_words_set = list(set(collected_words_list))
    return collected_words_set
    
def look_for_similar (offset, interval, debug = DEBUG):
    output_unigramm_json = []
    cursor_iterate = conn.cursor()
    request ="""SELECT word_id, ref_id,setting_id AS translation_id,
                jdesc ->>'tr' AS translate
                FROM content_words_lang
                WHERE (array_length(regexp_split_to_array(jdesc ->>'tr', '[ ''-]'), 1) = 1) AND (ref_id = 1) AND (word_id >= """ + str(offset) + """)
                ORDER BY word_id ASC
                limit """ + str(interval) 
    
    if debug:print(request)
    conn.rollback()
    cursor.execute(request)
    sim_words_dict = {}
    for row in cursor:
        if debug:print("word_id", row[0])
        word = row[3]
        word_id = row[0]
        eng_detection = re.findall("[a-zA-Z0-9]",word)
        if len(eng_detection) == 0:
            curr_json = {}
            
            #print(word_id)
            word_len = len(word)
            word_container = []
            p = morph.parse(word)[0]
            lemma = p.normal_form
            pos = p.tag.POS 
            if debug:print(lemma,pos)
            sim_words_dict[word] = look_inside_dict(word,lemma, pos,  word_container, word_len,1)
            if debug:print("SIMILAR WORDS FOR ", word, "\n",sim_words_dict[word])
            curr_json = {"word_id":word_id, "word":word, "ref_id":row[1],"setting_id":row[2], "simlar_words": sim_words_dict[word]}
            output_unigramm_json.append(curr_json)
    write_response(output_unigramm_json,offset, word_id)

    return word_id

word_id = START_WORD_ID
interval = 100
while word_id < FIN_WORD_ID:
    word_id = look_for_similar(word_id, interval)
    print(word_id,(word_id/FIN_WORD_ID)*100)
    time.sleep(0.1)
conn.close()