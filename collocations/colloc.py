from string import punctuation
full_punctuation = punctuation + "–" + "," + "»" + "«" + "…" +'’'

from ud_class import Model
import psycopg2
import copy
import json

conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
cursor = conn.cursor()

def read_text(path):
    raw_text = ''
    with open (path, 'r', encoding = "utf-8") as f:
        for line in f.readlines():
            raw_text += line + ' ' 
    return raw_text

def get_conllu_from_unite_line_text(text, model):
    sentences = model.tokenize(text)
    for s in sentences:
        model.tag(s)
        model.parse(s)
    conllu = model.write(sentences, "conllu")
    return conllu
    
def get_conllu_text_map(conllu_parsed_object):
    conllu_text_map = []
    conllu_sentence_map = []
    for line in conllu_parsed_object.split('\n'):
        if line:
            if line[0].isdigit():
                #print(line.split('\t'))
                conllu_sentence_map.append(line.split('\t'))
            else:
                if(len(conllu_sentence_map) > 0):
                    conllu_text_map.append(conllu_sentence_map)
                    conllu_sentence_map = []   
                    #print("appended")
    if(len(conllu_sentence_map) > 0):
        conllu_text_map.append(conllu_sentence_map)
    return conllu_text_map
    
def get_lemm_and_orig_text_from_udmap(conllu_map):
    lemm_sentences_list = []
    sentences_list = []
    for sentence in conllu_map:
        lemm_line = ''
        line = ''
        for word in sentence: 
            if (word[3] != 'PUNCT'):
                #print(word[2])
                clean_lemma = ''
                for char in word[2]:
                    if char not in full_punctuation:
                        clean_lemma += char.lower()
                lemm_line += clean_lemma + ' '
                line += word[1] + ' '
            else:
                lemm_line = lemm_line[:-1] + word[1]
                line = line[:-1] + word[1]

        lemm_sentences_list.append(lemm_line.strip())
        sentences_list.append(line.strip())
        #print()
    return lemm_sentences_list, sentences_list

def create_map(conllu_map):
    text_map = {'sentences':[]}
    for sentence in conllu_map:
        sentence_map = []
        for word in sentence: 
            if (word[3] != 'PUNCT'):
                clean_lemma = ''
                for char in word[2]:
                    if char not in full_punctuation:
                        clean_lemma += char.lower()
                word_struct = {"word":word[1],"lemma":clean_lemma}
                
                sentence_map.append(word_struct)
            else:
                sentence_map.append({"word":word[1],"lemma":word[1]})
        text_map['sentences'].append(sentence_map)
    return text_map


def get_colloc(ngr, words_list, handled_words_indexes, sentence_collected_collocation, debug = False):#присваивать по диту и потом cортировать по ключам
    if ngr <  len(words_list):
        for word_ind in range(ngr, len(words_list) + 1):
            #print("word_ind", word_ind)
            ngramm = ''
            ngramm_orig = ''
            sub_ind = []
            for word_sub_ind in range(word_ind - ngr, word_ind): 
                if word_sub_ind in handled_words_indexes:
                    if debug:print("ALREADY HANDLED")
                    ngramm = None
                    break
                sub_ind.append(word_sub_ind)
                #print("word_sub_ind", word_sub_ind)
                ngramm += words_list[word_sub_ind]['lemma'] + ' '
                ngramm_orig += words_list[word_sub_ind]['word'] + ' '
                if debug:print(ngramm)
            if ngramm:
                if debug:print(sub_ind)
                ngramm = ngramm.strip() 
                print(ngramm)
                cursor = conn.cursor()
                word_hash_request = """SELECT ('x'||substr(md5(translate(lower(btrim( ' """ + ngramm + """ ' )), concat(' -'''), '')), 1, 16))::bit(64)::bigint"""
                #print(word_hash_request)
                cursor.execute(word_hash_request)
                word_hash_req_result = cursor.fetchone()
                #print("word_hash", word_hash_req_result)
                get_word_from_hash_request = """SELECT * FROM public.content_words Where (word_hash = """ + str(word_hash_req_result[0]) + """)"""
                conn.rollback()
                cursor.execute(get_word_from_hash_request)
                word_from_hash = cursor.fetchone()
                if word_from_hash:
                    ngramm_orig = ngramm_orig.strip()
                    print("COLLOC FOUND", ngramm)
                    ngramm_lemmas_list = ngramm.split()
                    handled_words_indexes.extend(sub_ind)
                    sentence_collected_collocation[sub_ind[0]] = {'lemma' : ngramm, 'orig_text' : ngramm_orig}
                    if debug:print("sentence_collected_collocation", sentence_collected_collocation)
            if debug:print(ngramm)
 
#vector function here
def update_with_colloc_vectors(text_map_input):
    text_map = copy.deepcopy(text_map_input)
    #print(text_map)
    text_map['collocations'] = []
    for sentence in text_map['sentences']:
        sent_colloc = []
        sentence_collocations = {}
        handled_words_ind = []
        #print(colloc_db['4'])
        get_colloc(4, sentence, handled_words_ind,sentence_collocations)
        #print("handled_words_ind after qgramm", sorted(handled_words_ind))
        get_colloc(3, sentence, handled_words_ind, sentence_collocations)
        #print("handled_words_ind after trigramm", sorted(handled_words_ind))
        get_colloc(2, sentence, handled_words_ind, sentence_collocations)
        #print("handled_words_ind after bigramm", sorted(handled_words_ind))
        for ind in range (len(sentence)):
            if ind not in handled_words_ind:
                sentence_collocations[ind] =  {'lemma' : sentence[ind]['lemma'], 'orig_text' : sentence[ind]['word']}
        #print("FINAL COLLOCATIONS")
        #print(sentence_collocations)
        colloc_list = []
        #print(sorted (sentence_collocations))
        for i in sorted (sentence_collocations) : 
            sent_colloc.append(sentence_collocations[i])
        text_map['collocations'].append(sent_colloc)
    return text_map

def get_text_map(text, raw_text_input = False):
    model = Model('english-partut-ud-2.0-170801.udpipe')
    if raw_text_input == True:
        raw_text = text 
    else:
        raw_text = read_text(text)
    conllu = get_conllu_from_unite_line_text(raw_text, model)
    conllu_text_map = get_conllu_text_map(conllu)
    lemm_sentences,sentences_list = get_lemm_and_orig_text_from_udmap(conllu_text_map)
    text_map = create_map(conllu_text_map)
    sentence_map_colloc = update_with_colloc_vectors (text_map)

    """
    tf_idf_dict = get_tf_idf_dict (lemm_sentences)
    text_map = create_map(conllu_text_map, tf_idf_dict)
    sentence_map_dep =  get_dependencies(conllu_text_map, text_map)
    sentence_map_colloc = update_with_colloc_vectors (sentence_map_dep,colloc_db,unigramm_db)
    sentence_map_feat = features_extraction(sentence_map_colloc) 
    json_text_map = text_features_cal(sentence_map_feat, sentences_list, lemm_sentences)
    """
    return sentence_map_colloc

text = """US President Donald Trump has ordered an investigation into France's planned tax on tech giants - a move that could result in retaliatory tariffs.
His trade representative said the US was "very concerned" that the tax "unfairly targets American companies"."""

sentence_map_colloc = get_text_map(text, raw_text_input = True)

with open("text_map_improved_example.json", "w") as f:
    json.dump(sentence_map_colloc,f, indent = 4, ensure_ascii = False)

conn.close()