import psycopg2
import json
from Levenshtein import distance
import time
import random
import copy
#import pymorphy2
import re

#https://github.com/erayyildiz/LookupAnalyzerDisambiguator

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--letter_count_dict")
#parser.add_argument("-a", "--NGRAMMS_ALPHABET_PATH")
parser.add_argument("-s", "--START_WORD_ID")#60
parser.add_argument("-f", "--FIN_WORD_ID")#28796487
#parser.add_argument("-l", "--ngramm_len")
parser.add_argument("-r", "--save_location")
args = parser.parse_args()

START_WORD_ID = int(args.START_WORD_ID)#2716
FIN_WORD_ID = int(args.FIN_WORD_ID) #60 28575386
DEBUG = False

import spacy #port_spec
nlp = spacy.load("/Users/lilyakhoang/input/pt_core_news_sm-2.1.0/pt_core_news_sm/pt_core_news_sm-2.1.0")

#conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')
conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
cursor = conn.cursor()

#morph = pymorphy2.MorphAnalyzer()
with open(args.letter_count_dict,"r") as f:
    letter_count_dict = json.load(f)

def write_response (json_file, start_index, final_index, debug = DEBUG):
    file_name = args.save_location + str(start_index) + '-' + str(final_index) +'.json'
    if debug: print("\nNOW SAVING", file_name,'\n')
    with open(file_name, 'w', encoding = "utf-8") as outfile:
        json.dump(json_file, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)
    
def iterate_insde_dict(collected_words_list, handled_ids, word, lemma, pos,examined_word_len, letter_count_dict, search_range, debug = DEBUG):
    collected_words = 0
    #print(word, examined_word_len, "search_range", search_range)
    if str(examined_word_len) in letter_count_dict and examined_word_len > 2:
        compare_words = letter_count_dict[str(examined_word_len)]
        random.shuffle(compare_words)
        for word_compare_el in compare_words:
            word_compare = word_compare_el[0]
            if "unknown" not in word_compare_el[1]:#SPECIFIC
                pos_compare = word_compare_el[1]
            else:
                pos_compare = None
            lemm_comapre = word_compare_el[2]
            comp_word_id = word_compare_el[3]
            comp_ref_id = word_compare_el[4]
            comp_set_id = word_compare_el[5]
            if search_range > 3:
                pos_search_range = search_range
            else:
                pos_search_range = 1
            
            if pos and pos_compare:
                if distance(lemm_comapre, lemma) > 0 and distance(lemm_comapre, lemma)  <= search_range and distance(pos_compare, pos) <= pos_search_range and comp_word_id not in handled_ids:
                    if debug:print("FOUND VS POS", word,word_compare,lemma, lemm_comapre, pos,pos_compare)
                    collected_words_list.append({"word_id":comp_word_id, "ref_id":comp_ref_id,"setting_id":comp_set_id, "ngramm": word_compare})
                    handled_ids.append(comp_word_id)
                    collected_words += 1
                    if (collected_words > 10 or len(collected_words_list) > 12):break
            else:
                if distance(lemm_comapre, lemma) > 0 and distance(lemm_comapre, lemma)  <= search_range and comp_word_id not in handled_ids:
                    if debug:print("FOUND NON POS", word,word_compare,lemma, lemm_comapre)
                    collected_words_list.append({"word_id":comp_word_id, "ref_id":comp_ref_id,"setting_id":comp_set_id, "ngramm": word_compare})
                    handled_ids.append(comp_word_id)
                    collected_words += 1
                    if (collected_words > 10 or len(collected_words_list) > 12):break
    #print("collected_words_list",collected_words_list)
    return collected_words

def clean_list(orig_list):
    unique_words_list = []
    collected_words_list_new = []
    for word_el in orig_list:
        #print(word_el['ngramm'], word_el['ngramm'] not in unique_words_list)
        if word_el['ngramm'] not in unique_words_list:
            unique_words_list.append(word_el['ngramm'])
            collected_words_list_new.append(word_el)
    collected_words_list_clean = copy.deepcopy(collected_words_list_new)
    return collected_words_list_clean

def look_inside_dict(word, lemma, pos, collected_words_list, handled_ids, word_len, search_range,debug = DEBUG):
    if debug:print (word, "word_len", word_len, "search range", search_range)
    total_words = len(collected_words_list)
    if search_range > 7:
        word_len = 6
    if(word_len > 2):
        new_words_collected_count = iterate_insde_dict(collected_words_list, handled_ids,word, lemma, pos,word_len-1, letter_count_dict, search_range)
        total_words += new_words_collected_count
        new_words_collected_count = iterate_insde_dict(collected_words_list,handled_ids, word, lemma, pos,word_len, letter_count_dict, search_range)
        total_words += new_words_collected_count
    new_words_collected_count = iterate_insde_dict(collected_words_list,handled_ids, word, lemma, pos,word_len+1, letter_count_dict, search_range)
    total_words += new_words_collected_count
    if(word_len <= 2):
        new_words_collected_count = iterate_insde_dict(collected_words_list, handled_ids, word, lemma, pos,word_len+2, letter_count_dict, search_range)
        total_words += new_words_collected_count
    while total_words < 12:
        search_range += 1
        look_inside_dict(word, lemma, pos, collected_words_list,handled_ids, word_len, search_range)
        collected_words_list = clean_list(collected_words_list)
        
        total_words = len(collected_words_list)
        #if debug:print("len_after_recursion", len(list(set(collected_words_list))))
    collected_words_list = clean_list(collected_words_list)
    return collected_words_list
    
def look_for_similar (offset, interval, debug = DEBUG):
    output_unigramm_json = []
    cursor_iterate = conn.cursor()
    request ="""SELECT word_id, ref_id,setting_id AS translation_id,
                jdesc ->>'tr' AS translate
                FROM content_words_lang
                WHERE (array_length(regexp_split_to_array(jdesc ->>'tr', '[ ''-]'), 1) = 1) AND (ref_id = 3) AND (word_id >= """ + str(offset) + """) AND (word_rating > 35)
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
        #eng_detection = re.findall("[a-zA-Z0-9]",word)#rus_specific
        #if len(eng_detection) == 0:
        curr_json = {}
        #print(word_id)
        word_len = len(word)
        word_container = []
        for token in nlp(word):
            pos = token.pos_
            lemma = token.lemma_
            break

        if debug:print(lemma,pos)
        handled_ids = []
        start = time.time()
        sim_words_dict[word] = look_inside_dict(word,lemma, pos,  word_container, handled_ids, word_len,1)
        
        if debug:print("SIMILAR WORDS FOR ", word, "\n",sim_words_dict[word])
        curr_json = {"word_id":word_id, "ngramm":word, "ref_id":row[1],"setting_id":row[2], "simlar_words": sim_words_dict[word]}
        output_unigramm_json.append(curr_json)
        end = time.time()
        #print("handling word",word, end - start )
    write_response(output_unigramm_json,offset, word_id)
    return word_id

word_id = START_WORD_ID
interval = 50
reconnection_count = 0

while word_id < FIN_WORD_ID:
    word_id = look_for_similar(word_id, interval)
    try:
        word_id = look_for_similar(word_id, interval)
        word_id += 1
        print(word_id,(word_id/FIN_WORD_ID)*100)
        time.sleep(random.uniform(1,2))
    except:
        reconnection_count +=1
        if reconnection_count < 25:
            print("CRASHED ON ",word_id)
            cursor.close()
            conn.close()
            #conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')
            conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
            cursor = conn.cursor()
            #word_id = FIN_WORD_ID + 1
        else:
            print("CRASHED ON ",word_id, "reconnection count limit reached. BREAK")
            word_id = FIN_WORD_ID + 1
cursor.close()
conn.close()