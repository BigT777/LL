import psycopg2
import json
from tqdm import tqdm
import statistics
import multiprocessing 
import time
import random
from colloc.calculate_colocations import get_pos_filtered_colloc_from_corpus_list
import progressbar

DEBUG = False 
AMOUNT_OF_TEXTS_INSIDE_REQUEST = 50
START_WORD_ID = 44824
FIN_WORD_ID = 300000
conn = psycopg2.connect(dbname='pgprod', user='linguist', password='eDQGK0GCStlYlHNV', host='postgres.lingualeo-beta.com')
cursor = conn.cursor()

def write_response (json_file, start_index, debug = DEBUG):
    file_name = './save_jung_id/' + str(start_index) + '.json'
    print("\nNOW SAVING", file_name,'\n')
    with open(file_name, 'w', encoding = "utf-8") as outfile:
        json.dump(json_file, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)

def get_text_from_jungle_id(jungle_id_offset, debug = DEBUG):
    if debug: print("==========================================================================")
    texts_in_one_object = 0
    texts = []
    conn.rollback()
    request = """SELECT jdesc ->>'page_text' AS page_text, jungle_id FROM public.content_jungle_pages WHERE 
    jungle_id >= """ + str(jungle_id_offset) + """ ORDER BY jungle_id ASC LIMIT """ + str(AMOUNT_OF_TEXTS_INSIDE_REQUEST)
    if debug: print(request)
    cursor.execute(request)
    current_text =''   
    current_text_jungle_id = 0
    first_entry_passed = False

    #check_index = 0
    #start_index = check_index
    for row in cursor:
        if debug: print(row[1])
        if(row[1] != current_text_jungle_id and first_entry_passed == False):
            if debug: print("===first===")
            if debug: print(row[1], row[0][:100])
            current_text_jungle_id = row[1]
            current_text += ' ' + row[0]
            first_entry_passed = True
            next_id = int(row[1])
            
        elif(row[1] != current_text_jungle_id and first_entry_passed == True):
            if debug: print("===jungid finished===")
            next_id = int(row[1])
            break
        else:
            if debug: print("===ADD TEXT===")
            if debug: print(row[1], row[0][:100])
            current_text += ' ' + row[0]
    
    if debug: print('THE TEXT FOR OUTPUT WITH ID',current_text_jungle_id, "IS ", current_text[:100] )
    if debug: print("==========================================================================")
    if next_id == int(jungle_id_offset):#в случае большого текста
        next_id = int(jungle_id_offset) + 1
    return next_id, current_text

#22 - 622756 (jungle_id но он бывает случаются варианты когда дублируется пожтому   )
#TOTAL PAGES "2461750"
global_texts_list = []
start_jung_id = START_WORD_ID
texts_count = 0 
next_id = START_WORD_ID


def save_results(texts,start_jung_id, next_id):
    if DEBUG: print(len(texts), "TEXT WILL BE LIKE THAT", texts[0][:100])
    file_range = str(start_jung_id) + '_' + str(next_id-1)
    if DEBUG: print(file_range, " COLLOC CALC STARTED")
    bigramFreqTable, trigramFreqTable, quadgram_freq, filtered_bi, filtered_tri, bigramPMITable, trigramPMITable, quadragramPMITable, bigramChiTable, trigramChiTable=get_pos_filtered_colloc_from_corpus_list(texts,"en")
    #bigramFreqTable.to_csv('./save_jung_id/bigramFreqTable/bigramFreqTable_' + file_range + '.csv')
    #trigramFreqTable.to_csv('./save_jung_id/trigramFreqTable/trigramFreqTable_' + file_range + '.csv')
    #quadgram_freq.to_csv('./save_jung_id/quadgram_freq/quadgram_freq_' + file_range + '.csv')
    filtered_bi.to_csv('./save_jung_id/filtered_bi/filtered_bi_' + file_range + '.csv')
    filtered_tri.to_csv('./save_jung_id/filtered_tri/filtered_tri_' + file_range + '.csv')
    bigramPMITable.to_csv('./save_jung_id/bigramPMITable/bigramPMITable_' + file_range + '.csv')
    trigramPMITable.to_csv('./save_jung_id/trigramPMITable/trigramPMITable_' + file_range + '.csv')
    quadragramPMITable.to_csv('./save_jung_id/quadragramPMITable/quadragramPMITable_' + file_range + '.csv')
    bigramChiTable.to_csv('./save_jung_id/bigramChiTable/bigramChiTable_' + file_range + '.csv')
    trigramChiTable.to_csv('./save_jung_id/trigramChiTable/trigramChiTable_' + file_range + '.csv')
    
while next_id < FIN_WORD_ID:
    next_id, text = get_text_from_jungle_id(next_id)
    print(next_id, 'count = ', texts_count)
    global_texts_list.append(text)
    if texts_count % 5000 == 0 and texts_count != 0:
        save_results(global_texts_list,start_jung_id, next_id)
        global_texts_list = []
        start_jung_id = next_id
    texts_count += 1
if texts_count > 5000:
    ave_results(global_texts_list,start_jung_id, next_id)
conn.close()