import requests
import json
from bs4 import BeautifulSoup as bs
import time
import random
import re
import pandas as pd
import os
import numpy as np

from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer 
lemmatizer = WordNetLemmatizer()
from nltk.corpus import stopwords

import numpy as np
from tqdm.auto import tqdm


import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--start_from_lookup_index")
parser.add_argument("-t", "--end_at_lookup_index")
parser.add_argument("-s", "--save_loc")
parser.add_argument("-w", "--timeout")
args = parser.parse_args()


from pymystem3 import Mystem

mystem = Mystem()


from french_lefff_lemmatizer.french_lefff_lemmatizer import FrenchLefffLemmatizer
lemmatizer = FrenchLefffLemmatizer()

def fr_lemmatize(word):
    lemma = lemmatizer.lemmatize(word)
    return lemma
def preprocess_words(words_list, lemmatizer_func):
    start = time.time()
    preprocessed_words = []
    for word in words_list:
        lemma = lemmatizer_func(word['sence_word'].lower())
        word['sence_word'] = lemma
    #print("lemmat_time", time.time() - start)
        #print("lemma",lemma)
        #preprocessed_words.append(lemma)
    #return preprocessed_words
        

def get_wordnet_pos(treebank_tag):

    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None
    
def en_lemmatize(line):
    pos_tagged_ngramm = pos_tag(line.split())
    lemmatized_line_list = []
    for word_el in pos_tagged_ngramm:
        pos = get_wordnet_pos(word_el[1])
        if pos:
            lemma = lemmatizer.lemmatize(word_el[0], pos =pos)
        else:
            lemma = word_el[0]
        lemmatized_line_list.append(lemma)
    return ' '.join(lemmatized_line_list)

def ru_lemmatize(line):
    lemmas = mystem.lemmatize(line)
    return ''.join(lemmas)[:-1]
ru_lemmatize("Красивая мама красиво мыла раму")

def compare_pos(pos1, pos2):
    if pos1 == pos2:
        #print("abs eq", pos1, pos2)
        return True
    elif pos1 in pos2 or pos2 in pos1:
        #print("inclusive eq", pos1, pos2)
        return True
    #print("no eq", pos1, pos2)
    return False
def equate_empty_pos(pos1, pos2):
    if pos1 == '': 
        pos1 = pos2
        #print("pos1 eqauted")
    elif pos2 == '': 
        pos2 = pos1
        #print("pos2 eqauted")
    return pos1, pos2

def check_restiction(soup):
    for link in soup.find_all("section", attrs={"id" : "error-content"}):
        restrict = ['Your', 'access', 'is', 'temporarily', 'restricted']
        #print(link, "\\")
        for l in link.find_all("p"):
            count = 0 
            restict = False
            for word in l.text.strip().split()[:5]:
                #print(word, restrict[count])
                if word == restrict[count]:
                    restict = True
                else:
                    restict = False
                count += 1
            if restict == True:
                raise Exception('Restiction_limit!!!!!!!!!!!!!!')

def send_request_func(from_lang,to_lang, word, header_main, login, en_from_lang, en_to_lang):
    start = time.time()
    url = "https://context.reverso.net/перевод/" + from_lang + "-" + to_lang + "/" + word 
    #print("going to find word in", url)
    response = requests.get(url, headers=header_main, data = login)
    response.encoding = 'utf-8' 
    soup = bs(response.text, 'html.parser') 
    check_restiction(soup)
    #
    save_dir = os.path.join("/Users/nigula/LL/adjust_unigr_dict/lookup/reverso" + "_" + en_from_lang + "_" + en_to_lang,word + ".xls")
    file = open(save_dir, "wb")
    file.write(response.content)
    file.close()
    #print("saved to directory", save_dir)
    
    time.sleep(random.uniform(0.01,float(args.timeout)))
    #print("request_time",time.time() - start) 
    return soup

def get_definitions_reverso(word, from_lang, to_lang, print_output = False):
    start = time.time()
    login = {'inUserName': 'n.babakov@lingualeo.com', 'inUserPass': '33vec33'}
    header_main = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    senseword_list = []
    land_dict = {"русский":"ru","французский":"fr", "английский":"en"}
    try:
        word_dir = os.path.join("/Users/nigula/LL/adjust_unigr_dict/lookup/reverso" + "_" + land_dict[from_lang] + "_" + land_dict[to_lang],word + ".xls")
        infile = open(word_dir,"r")
        #print("found_word_in", word_dir)
        contents = infile.read()
        soup = bs(contents,'html.parser')
        found_in_folder = True
    except:
        found_in_folder = False
        soup = send_request_func(from_lang,to_lang, word, header_main, login, land_dict[from_lang], land_dict[to_lang])
    #print(soup.prettify())
    first_string_passed = False
    pos = ''
    for link in soup.find_all("a", attrs={"class" : "translation"}):
        #print(link.prettify())
        try:
            #print("||",link['data-pos'])
            pos = link['data-pos'][1:-1]
        except:
            pass
        if first_string_passed == True:
            sence_word = link.text.strip()
            if len(sence_word) >0:
                senseword_list.append({"sence_word":sence_word.lower(), "pos":pos})
            #print(sence_word)
        first_string_passed = True
        
    for link in soup.find_all("div", attrs={"class" : "translation"}):
        #print(link.prettify())
        try:
            #print("||",link['data-pos'])
            pos = link['data-pos'][1:-1]
        except:
            pass
        if first_string_passed == True:
            sence_word = link.text.strip()
            if len(sence_word) >0:
                senseword_list.append({"sence_word":sence_word.lower(), "pos":pos})
            #print(sence_word)
        first_string_passed = True
    if len (senseword_list) == 0:
        #print("turn to alternative marks")
        for link in soup.find_all("div", attrs={"lang" : "fr"}):
            try:
                #print("||",link['data-pos'])
                pos = link['data-pos'][1:-1]
            except:
                pass
            sence_word = link.text.strip()
            senseword_list.append({"sence_word":sence_word.lower(), "pos":pos})
            #print(link.prettify())
    #print("definiotns_time", time.time() - start)
    return senseword_list, found_in_folder

def get_two_target_lang_lists_intersection(list_1, list_2, lists_lang):
    overall_intersection = []
    cos_sim_dict ={}
    #overall_intersection
    for word_1 in list_1:
        for word_2 in list_2:
            #print(word_1, word_2)
            word_1['pos'], word_2['pos'] = equate_empty_pos(word_1['pos'], word_2['pos'])
            pos_eq = compare_pos(word_1['pos'],word_2['pos'])  
            if pos_eq == True and word_1['sence_word'] == word_2['sence_word']:
                #overall_intersection.append(word_1)
                cos_sim_dict[word_1['sence_word']] = []
    #print(cos_sim_dict)             
    #GETET INTERSECTION LIST
    for first_word in cos_sim_dict.keys():
        intersect_element = first_word
        for similar_word in cos_sim_dict[first_word]:
            intersect_element += " | " + similar_word
        overall_intersection.append(intersect_element)
    #print(time.time() - start, "passed get_two_target_lang_lists_intersection")
    return overall_intersection

def get_cross_translate_reverso(word_lang_1, lang_1, word_lang_2, lang_2, target_lang, lemmatizer_func):
    found_in_folder_count = 0
    lang_1_to_target_words_dict, found_in_folder = get_definitions_reverso(word_lang_1, lang_1, target_lang, print_output=True)
    if found_in_folder == True: found_in_folder_count += 1
    preprocess_words(lang_1_to_target_words_dict, lemmatizer_func)
    
    lang_2_to_target_words_dict, found_in_folder = get_definitions_reverso(word_lang_2, lang_2, target_lang, print_output=True)
    if found_in_folder == True: found_in_folder_count += 1
    preprocess_words(lang_2_to_target_words_dict, lemmatizer_func)
    
    #print("lang_1_to_target_words_dict", lang_1_to_target_words_dict,"\n")
    #print("lang_2_to_target_words_dict", lang_2_to_target_words_dict)
    
    intersected_elements = get_two_target_lang_lists_intersection(lang_1_to_target_words_dict, lang_2_to_target_words_dict,
                                                                 target_lang)
    
    if len(intersected_elements) == 0:intersected_elements.append("no_equality")
    return intersected_elements, found_in_folder_count

def get_multilang_from_df(df, lookup_from, lookup_to, target_lang, target_lang_lemmatizer_func, save_location, start_from_df_ind = None, finish_index = None):
    land_dict = {"русский":"ru","французский":"fr", "английский":"en"}
    eng_word_list = []
    lang_1_word_list = []
    lang_2_word_list = []
    eng_word = 'first_word'
    save_triple_path = land_dict[lookup_from] + '_' + land_dict[lookup_to] + '_' + land_dict[target_lang] + '_'
    current_range_triple = save_triple_path + save_location
    overall_found_in_folder_count = 0
    if start_from_df_ind == None:
        start = True
    else:
        start = False
    
    #for df_ind in tqdm(range(len(df))):
    absolute_count = 0 
    except_count = 0
    real_count = 0
    #totral_rows = int(finish_index) - int(start_from_df_ind)
    for index, row in tqdm(df.iterrows(), total=int(finish_index)):
        try:
            if str(absolute_count) == str(start_from_df_ind):
                start = True
            if str(absolute_count) == str(finish_index):
                #print("FINISHED_ITERATE_COUNT")
                break
            if start == True:
                #if eng_word != row["word"]: print("\n************************************\n")
                eng_word = row["word"]
                #if eng_word == "trajet": start = True
                #if start == True:
                loc_1_word = row["local_word"]
                #print(eng_word, loc_1_word)
                sense_intersect, found_in_folder_count = get_cross_translate_reverso(eng_word, lookup_from, loc_1_word, lookup_to, target_lang, target_lang_lemmatizer_func)
                overall_found_in_folder_count += found_in_folder_count
                #sense_intersect = get_cross_translate_yand(eng_word, "en", loc_1_word,"ru", "fr", fr_lemmatize)
                #print("\n SENSE_INTERSECTION ", sense_intersect)
                for sense_intersect_element in sense_intersect:
                    eng_word_list.append(eng_word)
                    lang_1_word_list.append(loc_1_word)
                    lang_2_word_list.append(sense_intersect_element)

                if absolute_count % 200 == 0 and absolute_count != int(start_from_df_ind):
                    print(overall_found_in_folder_count/(real_count*2),"found offline")
                    print(overall_found_in_folder_count,"overall_found_in_folder_count",real_count, "total_iterations" )
                    save_path = os.path.join("/Users/nigula/LL/adjust_unigr_dict/reverse_connected_dicts/cross_barbos",
                                current_range_triple, str(absolute_count) + ".csv")
                    print("saved_at",save_path)
                    data = pd.DataFrame(list(zip(eng_word_list, lang_1_word_list,lang_2_word_list)),
                                columns =[land_dict[lookup_from], land_dict[lookup_to], land_dict[target_lang]])
                    data.to_csv(save_path)
                real_count += 1  
        except Exception as ex:
            print(ex)
            except_count += 1
            print("will_sleep_for", 1 * except_count)
            time.sleep(30 * except_count)
            if except_count > 200:
                print("TOO_MANY_EXCEPTIONS")
                break
        absolute_count += 1     
        
                
    data = pd.DataFrame(list(zip(eng_word_list, lang_1_word_list,lang_2_word_list)),
                        columns =[land_dict[lookup_from], land_dict[lookup_to], land_dict[target_lang]])
    
    return data

#df_din = get_multilang_from_df(df_en_ru_yandex, "английский", "русский", "французский", fr_lemmatize)
#df_din.head()

df_lookup_yandex = pd.read_csv("/Users/nigula/LL/adjust_unigr_dict/lookup results/yandex_lookup_en_ru_wordforms.csv")

df = get_multilang_from_df(df_lookup_yandex, "английский", "русский", "французский", fr_lemmatize, start_from_df_ind = args.start_from_lookup_index, finish_index = args.end_at_lookup_index, save_location = args.save_loc)

df.to_csv("df_en_ru_fr_wf.csv")

