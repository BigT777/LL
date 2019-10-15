import psycopg2
import re
import time
import random
from word_forms.word_forms import get_word_forms
import json  
from nltk.stem import WordNetLemmatizer 
import nltk 
from nltk.corpus import wordnet
lemmatizer = WordNetLemmatizer() 
conn = psycopg2.connect(dbname='pgstage', user='linguist', password='eDQGK0GCStlYlHNV', host='192.168.122.183')
#conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
cursor = conn.cursor()

#OPTIONAL STUFF 1365  98546187

dict_path = "unigramms_unique.json"
START_WORD_ID = 500000
FIN_WORD_ID = 102396352#-60 102401842
ngramm_len = 1
DEBUG = False
save_location = './save_results/'
save_drop_location = './save_drop_results/'

with open( dict_path,"r") as f:
    data = json.load(f)
    dct_mixed_words = {}
    for el in data:
        dct_mixed_words[el['word']] = el['simlar_words']
    dct_mixed_words['specifications']

def write_response (json_file, start_index, final_index, drop , debug = DEBUG):
    if drop == False:
        file_name = save_location + str(start_index) + '-' + str(final_index) +'.json'
    else:
        file_name = save_drop_location + str(start_index) + '-' + str(final_index) +'.json'
    if debug: print("\nNOW SAVING", file_name,'\n')
    with open(file_name, 'w', encoding = "utf-8") as outfile:
        json.dump(json_file, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)

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

def extract_variants_from_dict(dct):
    wordforms_list = []
    for wordform_type in dct.keys():
        for wordform in dct[wordform_type]:
            #print(wordform)
            if len(wordform.split()) == 1:
                wordforms_list.append(wordform)
    return set(wordforms_list)

def get_wordforms(word):
    MINIMAL_WORDFORMS_REQ = 6
    regex = re.compile('[^a-zA-Z]')
    clean_word = regex.sub('', word)
    #print(clean_word)
    if len(clean_word) > 0:
        pos_tagged_ngramm = nltk.pos_tag([clean_word])
        for word_el in pos_tagged_ngramm:
            #print(word_el)
            pos = get_wordnet_pos(word_el[1])
            if pos:
                lemma = lemmatizer.lemmatize(word_el[0], pos =pos)
            else:
                lemma = word_el[0]
            break
        if clean_word ==  lemma:
            wordforms_dict = get_word_forms(clean_word)
            wordform_set = extract_variants_from_dict(wordforms_dict)
        else:
            wordforms_dict = get_word_forms(clean_word)
            wordform_set = extract_variants_from_dict(wordforms_dict)
            
            wordforms_lemma_dict = get_word_forms(lemma)
            wordform_set_from_lemma = extract_variants_from_dict(wordforms_lemma_dict)
            wordform_set = wordform_set.union(wordform_set_from_lemma)

        if len(wordform_set) < MINIMAL_WORDFORMS_REQ:
            if lemma in dct_mixed_words:
                more_words_number = MINIMAL_WORDFORMS_REQ - len(wordform_set)
                add_words_list = dct_mixed_words[lemma][:more_words_number]
                #print("additional words", add_words_list)
                add_words_list = set(add_words_list[:6])
                wordform_set = wordform_set.union(add_words_list)
            #else:
                #print("NOT_ENOUGH_WORDS_AND_NOT_ENOUGH_MIXED_WORDS",word)
        wordform_list = list(wordform_set)
        if word in wordform_list:
            wordform_list.remove(word)
        return wordform_list
    else:
        return []

def look_for_similar (word_id_offset, interval, debug = DEBUG):

    
    request = """SELECT word_id, jdesc->>'wd' AS ngram FROM public.content_words
        WHERE array_length(regexp_split_to_array(content_words.jdesc->>'wd', '[ ''-]'), 1) = 1 and 
        word_id > """ + str(word_id_offset) + """ and word_hash != 0 ORDER BY word_id
        LIMIT """ + str(interval)
    output_unigramm_json = []
    dropped_words_output_unigramm_json = []
    cursor.execute(request)
    for row in cursor:
        word_id = row[0]
        word = row[1]
        curr_json = {}
        curr_json = {"word_id":row[0], "word":word}
        #print(word)
        wordforms = get_wordforms(word)
        curr_json['wordform'] = wordforms
        if len(wordforms) > 1:
            output_unigramm_json.append(curr_json)
        else:
            print("drop", word, wordforms)
            dropped_words_output_unigramm_json.append(word)
    write_response(output_unigramm_json,word_id_offset, word_id, drop = False)
    write_response(dropped_words_output_unigramm_json,word_id_offset, word_id, drop = True)
    return word_id

# trigram word id 67 102394810
interval = 75
word_id = START_WORD_ID

reconnection_count = 0
while word_id < FIN_WORD_ID:
    word_id = look_for_similar(word_id, interval)
    try:
        word_id = look_for_similar(word_id, interval)
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