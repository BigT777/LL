import pandas as pd
import nltk
from nltk import wordnet
#from nltk.stem import WordNetLemmatizer
#from nltk.corpus import wordnet
from Levenshtein import distance
import psycopg2
import random
import json 
from string import punctuation
import time
import re

from nltk.corpus import stopwords
stopWords = set(stopwords.words('portuguese'))#port_specific
import spacy #port_spec
nlp = spacy.load("/Users/lilyakhoang/input/pt_core_news_sm-2.1.0/pt_core_news_sm/pt_core_news_sm-2.1.0")


# 2 -- -32170257

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--NGRAMMS_PATH")
parser.add_argument("-a", "--NGRAMMS_ALPHABET_PATH")
parser.add_argument("-s", "--START_WORD_ID")
parser.add_argument("-f", "--FIN_WORD_ID")
parser.add_argument("-l", "--ngramm_len")
parser.add_argument("-r", "--save_location")
args = parser.parse_args()

#lemmatizer = WordNetLemmatizer()
conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')#
#conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
cursor = conn.cursor()
#punctuation_small_set = punctuation.replace("-","")
#punctuation_small_set = punctuation_small_set.replace("'","")


#rus_specific
NGRAMMS_PATH = args.NGRAMMS_PATH
NGRAMMS_ALPHABET_PATH = args.NGRAMMS_ALPHABET_PATH

START_WORD_ID = int(args.START_WORD_ID)
FIN_WORD_ID = int(args.FIN_WORD_ID)#102396352
ngramm_len = args.ngramm_len
DEBUG = False
save_location = args.save_location

with open( NGRAMMS_PATH,"r") as f:
    NGRAMM = json.load(f)

with open(NGRAMMS_ALPHABET_PATH,"r") as f:
    NGRAMM_ALPHA_DICT = json.load(f)

def write_response (json_file, start_index, final_index, debug = DEBUG):
    file_name = save_location + str(start_index) + '-' + str(final_index) +'.json'
    if debug: print("\nNOW SAVING", file_name,'\n')
    with open(file_name, 'w', encoding = "utf-8") as outfile:
        json.dump(json_file, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)

def get_orig_string (word_pos_list):
    orig_string = ''
    for el in word_pos_list:
        word = el.split("_")[0]
        orig_string += word + ' '
    orig_string = orig_string.strip()
    return orig_string


def get_lemmas_list (word_pos_list):
    lemma_list = []
    for el in word_pos_list:
        lemma = el.split("_")[2]
        lemma_list.append(lemma)
    return lemma_list
def get_pos_string (word_pos_list):
    pos_string = ''
    for el in word_pos_list:
        pos = el.split("_")[1]
        pos_string += pos
    return pos_string

def copare_lemmas_lists(compared_lemmas, lemmas_from_list, search_range, debug = DEBUG):
    same_words_count = 0
    total_ngramm_len = len(compared_lemmas)
    for lemma_comp in compared_lemmas:
        for lemma_list in lemmas_from_list:
            if lemma_comp.lower() == lemma_list.lower():
                same_words_count += 1
                if same_words_count == total_ngramm_len:
                    if debug:print("SAME WORD")
                    return False
            elif distance(lemma_comp, lemma_list) > 0 and distance(lemma_comp, lemma_list) <= search_range:
                continue
            else:
                if debug:print("TOO MUCH lemmas DIFFERENCE")
                return False
    return  True

def look_one_similar_word(orig_lemma_list, comp_lemma_list, debug = DEBUG):
    if debug:print("to be compared", orig_lemma_list,comp_lemma_list )
    similar_words_count = 0
    for orig in orig_lemma_list:
        if orig not in stopWords:
            for comp in comp_lemma_list:
                if orig == comp:
                    similar_words_count += 1
    if similar_words_count == 1: 
        if debug: print("similar not equal", orig_lemma_list,comp_lemma_list )
        return True
    else: 
        if debug: print("NOtsimilarnotequal")
        return False
def compare_word_pos_lemma_list(compared_wpl, from_list_wpl, search_range, look_for_one_similar_word, debug = DEBUG):
    if debug: print("COMPARED",compared_wpl, "FROM LIST",from_list_wpl, "SEARCH RANGE",search_range)
    compared_lemma_list = get_lemmas_list(compared_wpl)
    from_list_lemma_list = get_lemmas_list(from_list_wpl)

    if look_for_one_similar_word:
         similar_search = look_one_similar_word(compared_lemma_list, from_list_lemma_list)
         return similar_search
    compared_pos_string = get_pos_string(compared_wpl)
    from_list_pos_string = get_pos_string(from_list_wpl)
    if debug:print(compared_lemma_list, from_list_lemma_list, compared_pos_string,from_list_pos_string)
    pos_check = False
    if distance(compared_pos_string, from_list_pos_string) > 0 and distance(compared_pos_string, from_list_pos_string) <= search_range:
        if debug: print("POS OK")
        pos_check = True
    else:
        if debug: print("TOO MUCH POS DIFFERENCE")
    lemmas_check = copare_lemmas_lists(compared_lemma_list, from_list_lemma_list, search_range)
    
    if pos_check == True and lemmas_check == True:
        if debug: print("all checks OK")
        return True

def get_word_pos_lemma_list(clean_ngramm):

    final_ngramm = []
    tkn = nltk.word_tokenize(clean_ngramm)
    #print(tkn)
    for word in tkn:
        for token in nlp(word):
            pos = token.pos_
            lemma = token.lemma_
            break

        #print(lemma,pos)
        
        element = word + "_" + pos + "_" + lemma
        final_ngramm.append(element)
    return final_ngramm


def check_strange_sim_beg(ngramm, debug = DEBUG):
    ngramm_split = ngramm.split()
    first_let = ngramm_split[0][0]
    for word in ngramm_split:
        if word[0] != first_let:
            if debug: print("no similar")
            return False
    if debug: print("strange_sim_beg_detected",ngramm)
    return True

def look_for_similar (word_id_offset, interval, similar_ngramms_list, debug = DEBUG):

    
    start = time.time()
    request ="""SELECT word_id, ref_id,setting_id AS translation_id,
                jdesc ->>'tr' AS translate
                FROM content_words_lang
                WHERE (array_length(regexp_split_to_array(jdesc ->>'tr', '[ ''-]'), 1) =""" + str(ngramm_len) + """) AND (ref_id = 3) AND (word_id >= """ + str(word_id_offset) + """) AND (word_rating > 10)
                ORDER BY word_id ASC
                limit """ + str(interval)
    #print(request)
    #conn.rollback()
    
    cursor.execute(request)
    end = time.time()
    #print("request time", end - start)
    abs_eq_search_time = 0
    elactic_search_time = 0
    random_search_time = 0
    output_unigramm_json = []

    start_abs = time.time()
    for row in cursor:
        
        curr_json = {}
        word_id = row[0]
        ngramm = row[3]

        handled_ID = []
        handled_ID.append(int(word_id))        
        clean_ngramm = ''
        for char in ngramm:
            if char not in punctuation:#punctuation_small_set
                clean_ngramm += char
            else:
                clean_ngramm += ' '
        clean_ngramm = clean_ngramm.strip()
        random.shuffle(similar_ngramms_list)
        word_pos_lemma_list = get_word_pos_lemma_list(clean_ngramm)
        collected_similar_ngramms = []
        collected_similar_ngramms_count = 0
        
        start = time.time()

        first_letters_list = []
        for word in clean_ngramm.split():
            first_two_el = min(2,len(word))
            first_two_letters = word[:first_two_el]
            first_letters_list.append(first_two_letters)
        for first_letters in first_letters_list:
            if debug:print("====ABSOLUTE EQUALITY SEARCH STARTED=====")
            if (first_letters in NGRAMM_ALPHA_DICT):
                compare_list = NGRAMM_ALPHA_DICT[first_letters]
                for similar_ngramm_index in range(len(compare_list)):
                    similar_ngramm = compare_list[similar_ngramm_index]
                    orig_line = get_orig_string(similar_ngramm)
                    strange_similar_beginning_of_similar_ngrmm = check_strange_sim_beg(orig_line)
                    if strange_similar_beginning_of_similar_ngrmm == False :
                        if debug:print(orig_line, "passed sim beg filter")
                        comp_result = compare_word_pos_lemma_list(word_pos_lemma_list, similar_ngramm, search_range = None, look_for_one_similar_word = True)
                        similar_ngramm_id = int(similar_ngramm[0].split("_")[3])
                        if comp_result == True and similar_ngramm_id not in handled_ID:
                            
                            if len(orig_line) > 5 and "str" in str(type(orig_line)):
                                if debug: print(similar_ngramm[0].split("_"))
                                
                                collect_sim_ngr = {"word_id":similar_ngramm[0].split("_")[3], "ref_id":similar_ngramm[0].split("_")[4],"setting_id":similar_ngramm[0].split("_")[5],"ngramm":orig_line}
                                handled_ID.append(int(similar_ngramm_id))
                                collected_similar_ngramms.append(collect_sim_ngr)
                                collected_similar_ngramms_count += 1
                                if debug:print("SIMILAR COLLECTED",collected_similar_ngramms_count )
                                if collected_similar_ngramms_count >= 12:
                                    break
                            else:
                                if debug: print("NOT MEET REQUIREMENTS", orig_line,len(orig_line),type(orig_line))
            end = time.time()
            abs_eq_search_time += end - start
            #print("first letter dict iter", end - start)
            search_range = 1
            if debug and collected_similar_ngramms_count < 12: print("====ELASTIC SEARCH STARTED=====")

            start = time.time()
            similar_ngramm_num_in_list = 0 
            while collected_similar_ngramms_count < 12 and search_range < 10 and similar_ngramm_num_in_list < len(similar_ngramms_list):
                similar_ngramm = similar_ngramms_list[similar_ngramm_num_in_list]
                #for similar_ngramm in similar_ngramms_list:
                """
                if search_range == 0:
                    similar_ngramm = similar_ngramms_list[similar_ngramm_index]
                    comp_result = compare_word_pos_lemma_list(word_pos_lemma_list, similar_ngramm, search_range, look_for_one_similar_word = True)
                """
                similar_ngramm_id = int(similar_ngramm[0].split("_")[3])
                if (similar_ngramm_id not in handled_ID):
                    comp_result = compare_word_pos_lemma_list(word_pos_lemma_list, similar_ngramm, search_range, look_for_one_similar_word = False) 
                    if comp_result == True:
                        handled_ID.append(int(similar_ngramm_id))
                        orig_line = get_orig_string(similar_ngramm)
                        strange_similar_beginning_of_similar_ngrmm = check_strange_sim_beg(orig_line)
                        if strange_similar_beginning_of_similar_ngrmm == False :
                            if debug: print(orig_line, "passed sim beg filter")
                            if len(orig_line) > 5 and "str" in str(type(orig_line)):
                                collect_sim_ngr = {"word_id":similar_ngramm[0].split("_")[3], "ref_id":similar_ngramm[0].split("_")[4],"setting_id":similar_ngramm[0].split("_")[5],"ngramm":orig_line}
                                collected_similar_ngramms.append(collect_sim_ngr)
                                collected_similar_ngramms_count += 1
                                if debug: print("SIMILAR COLLECTED",collected_similar_ngramms_count )
                                if collected_similar_ngramms_count >= 12:
                                    break
                else:
                    if debug: print("INDEX ALREADY HANDLED")
                search_range += 1
                similar_ngramm_num_in_list += 1
            end = time.time()
            elactic_search_time += end - start
            #print("elastic search time", end - start)

            similar_ngramm_index = 0
            if debug and collected_similar_ngramms_count < 12 : print("====RANDOM SEARCH STARTED=====")

            start = time.time()
            while collected_similar_ngramms_count < 12 and similar_ngramm_index < len(similar_ngramms_list):
                similar_ngramm = similar_ngramms_list[similar_ngramm_index]
                similar_ngramm_id = int(similar_ngramm[0].split("_")[3])
                if (similar_ngramm_id not in handled_ID):
                    orig_line = get_orig_string(similar_ngramm)
                    if len(orig_line) > 5 and "str" in str(type(orig_line)):
                        collect_sim_ngr = {"word_id":similar_ngramm[0].split("_")[3], "ref_id":similar_ngramm[0].split("_")[4],"setting_id":similar_ngramm[0].split("_")[5],"ngramm":orig_line}
                        collected_similar_ngramms.append(collect_sim_ngr)
                        collected_similar_ngramms_count += 1
                        if debug: print("SIMILAR COLLECTED",collected_similar_ngramms_count )
                similar_ngramm_index += 1
            if debug: 
                print(collected_similar_ngramms)
                #print("========")
        curr_json = {"word_id":word_id, "ngramm":ngramm, "ref_id":row[1],"setting_id":row[2],"simlar_words": collected_similar_ngramms}
        output_unigramm_json.append(curr_json)
        end = time.time()
        random_search_time += end - start
            #print("elastic search time", end - start)
    write_response(output_unigramm_json,word_id_offset, word_id)

    end_overall = time.time()
    
    overall_iterate_time = end_overall - start_abs
    if debug: 
        print("first letter dict iter", abs_eq_search_time, abs_eq_search_time/overall_iterate_time)
        print("elastic search time", elactic_search_time, elactic_search_time/ overall_iterate_time)
        print("random search time", random_search_time, random_search_time/ overall_iterate_time)
        print("iteration time", overall_iterate_time)
    return word_id

# trigram word id 67 102394810
interval = 75
word_id = START_WORD_ID

reconnection_count = 0
while word_id < FIN_WORD_ID:
    #word_id = look_for_similar(word_id, interval, NGRAMM)
    try:
        word_id = look_for_similar(word_id, interval, NGRAMM)
        word_id += 1
        print(word_id,(word_id/FIN_WORD_ID)*100)
        time.sleep(random.uniform(1,3))
    except:
        reconnection_count +=1
        if reconnection_count < 25:
            print("CRASHED ON ",word_id)
            cursor.close()
            conn.close()
            conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')
            #conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
            cursor = conn.cursor()
            #word_id = FIN_WORD_ID + 1
        else:
            print("CRASHED ON ",word_id, "reconnection count limit reached. BREAK")
            word_id = FIN_WORD_ID + 1
cursor.close()
conn.close()