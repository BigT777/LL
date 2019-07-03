import psycopg2
import json
import nltk 
from string import punctuation
full_punctuation = punctuation + "–" + "," + "»" + "«" + "…" +'’'
from nltk.stem import WordNetLemmatizer 
lemmatizer = WordNetLemmatizer() 

from nltk.corpus import wordnet

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

conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')

SOURCE_NGRAMM = '/Users/nigula/Desktop/colloc_5k_backup/big_trigramms_list.json'
BOTTOM_word_id = 0
UPPER_word_id = 102401841#102401841
ngramm_len = 3
DEBUG = False
save_location = './save/tri/' 
with open(SOURCE_NGRAMM, "r") as f:
    ngramm_reference = json.load(f)

def write_response (json_file, start_index, final_index, debug = DEBUG):
    file_name = save_location + str(start_index) + '-' + str(final_index) +'.json'
    if debug: print("\nNOW SAVING", file_name,'\n')
    with open(file_name, 'w', encoding = "utf-8") as outfile:
        json.dump(json_file, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)

def look_for_similar (word_id_offset, interval, debug = DEBUG):
    request = """SELECT word_id, word_lemma, word_id, jdesc->>'wd' AS word_value
    FROM public.content_words WHERE(word_hash != 0) AND (((array_length(regexp_split_to_array(content_words.jdesc->>'wd', '[ ''-]'), 1) = """ + str(ngramm_len) + """))) AND (word_id >=""" + str(word_id_offset) + """)
    ORDER BY word_id ASC LIMIT """ + str(interval) 
    if debug == True: print(request)
    conn.rollback()
    cursor = conn.cursor()
    cursor.execute(request)
    output_unigramm_json = []
    saved_ids = []
    for row in cursor:
        ngramm_ok = False
        raw_ngramm = row[3]
        ngramm = ''
        for char in raw_ngramm:
            if char not in full_punctuation:
                ngramm += char.lower()
        word_id = row[0]
        rating = row[2]
        if rating > 100:
            if ngramm in ngramm_reference:
                ngramm_ok = True
                if debug == True: print("SELECTED FROM NGRAMM",ngramm)
                reason = "SELECTED FROM NGRAMM"
            else:
                text = nltk.word_tokenize(ngramm)
                pos_tagged_ngramm = nltk.pos_tag(text)
                if len (pos_tagged_ngramm) == 1:
                    #print(pos_tagged_ngramm[0][0])
                    if len(pos_tagged_ngramm[0][0]) > 2:ngramm_ok = True
                    if debug == True: print("SELECTED_UNIGRAMM",ngramm)
                    reason = "SELECTED_UNIGRAMM"
                    
                elif len (pos_tagged_ngramm) == 2:
                    noun_adj = ("NN","JJ","RP","RB","RBS", "NNS","NNP","NNPS","JJR","JJS","DT","PDT","VBN","VB","VBD","VBG","VBZ","VBP","IN")
                    if pos_tagged_ngramm[0][1] in noun_adj and pos_tagged_ngramm[0][1]:
                        if debug == True: print("SELECTED FROM POS",ngramm)
                        reason = "SELECTED FROM POS"
                        ngramm_ok = True
                    lemmatized = ''
                    for word_el in pos_tagged_ngramm:
                        pos = get_wordnet_pos(word_el[1])
                        if pos:
                            lemma = lemmatizer.lemmatize(word_el[0], pos =pos)
                        else:
                            lemma = word_el[0]
                        lemmatized += lemma + ' '
                    lemmatized = lemmatized.strip()
                    if lemmatized in ngramm_reference:
                        ngramm_ok = True
                        if debug == True: print("SELECTED AFTER LEMMATIZATION",ngramm)
                        reason = "SELECTED AFTER LEMMATIZATION"
                elif len (pos_tagged_ngramm) == 3:
                    noun_adj = ("PRP","CC","NN","JJ","RP","RB","RBS", "NNS","NNP","NNPS","JJR","JJS","DT","PDT","VBN","VB","VBD","VBG","VBZ","VBP","IN")
                    if pos_tagged_ngramm[0][1] in noun_adj and pos_tagged_ngramm[0][1]:
                        if debug == True: print("SELECTED FROM POS",ngramm)
                        reason = "SELECTED FROM POS"
                        ngramm_ok = True
                    lemmatized = ''
                    for word_el in pos_tagged_ngramm:
                        pos = get_wordnet_pos(word_el[1])
                        if pos:
                            lemma = lemmatizer.lemmatize(word_el[0], pos =pos)
                        else:
                            lemma = word_el[0]
                        lemmatized += lemma + ' '
                    lemmatized = lemmatized.strip()
                    if lemmatized in ngramm_reference:
                        ngramm_ok = True
                        if debug == True: print("SELECTED AFTER LEMMATIZATION",ngramm)
                        reason = "SELECTED AFTER LEMMATIZATION"
            if ngramm_ok == True:
                saved_ids.append({"word_id":word_id, "ngramm":ngramm,"raw_ngramm":raw_ngramm,"reason":reason})
            else:
                #if debug == True: print("NOT_OK",pos_tagged_ngramm)
                print("NOT_OK",pos_tagged_ngramm)
        
    write_response(saved_ids,word_id_offset, word_id)
    return word_id
         
interval = 50
word_id = BOTTOM_word_id

while  word_id < UPPER_word_id:
    word_id = look_for_similar(word_id, interval)
    word_id += 1
    print(word_id)
conn.close()