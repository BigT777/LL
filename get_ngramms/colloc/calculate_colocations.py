
from tqdm import tqdm
import pandas as pd
import nltk

from .ud_class import Model
from string import punctuation
full_punctuation = punctuation + "–" + "," + "»" + "«" + "…" +'’' + '—'
from nltk.metrics.association import QuadgramAssocMeasures
from nltk.corpus import wordnet 
from nltk.stem import WordNetLemmatizer
from pymystem3 import Mystem




#common functions
def get_freq_colloc(text_split):

    bigramFinder = nltk.collocations.BigramCollocationFinder.from_words(text_split)
    trigramFinder = nltk.collocations.TrigramCollocationFinder.from_words(text_split)
    quadgramFinder = nltk.collocations.QuadgramCollocationFinder.from_words(text_split)
    

    bigram_freq = bigramFinder.ngram_fd.items()
    bigramFreqTable = pd.DataFrame(list(bigram_freq), columns=['bigram','freq']).sort_values(by='freq', ascending=False)
    #trigrams
    trigram_freq = trigramFinder.ngram_fd.items()
    trigramFreqTable = pd.DataFrame(list(trigram_freq), columns=['trigram','freq']).sort_values(by='freq', ascending=False)

    quadgram_freq = quadgramFinder.ngram_fd.items()
    quadragramFreqTable = pd.DataFrame(list(quadgram_freq), columns=['quadgramF','freq']).sort_values(by='freq', ascending=False)

    return bigramFreqTable, trigramFreqTable, quadragramFreqTable

def get_pmi_and_chi_colloc(text_split):
    bigrams = nltk.collocations.BigramAssocMeasures()
    trigrams = nltk.collocations.TrigramAssocMeasures()
    quadragram = QuadgramAssocMeasures()

    bigramFinder = nltk.collocations.BigramCollocationFinder.from_words(text_split)
    trigramFinder = nltk.collocations.TrigramCollocationFinder.from_words(text_split)
    quadgramFinder = nltk.collocations.QuadgramCollocationFinder.from_words(text_split)
    
    bigramFinder.apply_freq_filter(10)
    trigramFinder.apply_freq_filter(5)
    quadgramFinder.apply_freq_filter(3)

    bigramPMITable = pd.DataFrame(list(bigramFinder.score_ngrams(bigrams.pmi)), columns=['bigram','PMI']).sort_values(by='PMI', ascending=False)
    trigramPMITable = pd.DataFrame(list(trigramFinder.score_ngrams(trigrams.pmi)), columns=['trigram','PMI']).sort_values(by='PMI', ascending=False)
    quadragramPMITable = pd.DataFrame(list(quadgramFinder.score_ngrams(quadragram.pmi)), columns=['quadragram','PMI']).sort_values(by='PMI', ascending=False)


    bigramChiTable = pd.DataFrame(list(bigramFinder.score_ngrams(bigrams.chi_sq)), columns=['bigram','chi-sq']).sort_values(by='chi-sq', ascending=False)
    trigramChiTable = pd.DataFrame(list(trigramFinder.score_ngrams(trigrams.chi_sq)), columns=['trigram','chi-sq']).sort_values(by='chi-sq', ascending=False)

    return bigramPMITable, trigramPMITable, quadragramPMITable, bigramChiTable, trigramChiTable



#POS filter approach
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
    
    lemm_sentences_list.append(lemm_line.strip())
    sentences_list.append(line.strip())
    #print()
    return lemm_sentences_list, sentences_list

def assign_pos_index(conllu_text_map):
    sentences_tagged = []
    for sentence in conllu_text_map:
        one_sentence_tagged = ''
        for word in sentence:
            if word[3] != "PUNCT":
                clean_lemma = ''
                for char in word[2]:
                    if char not in full_punctuation:
                        clean_lemma += char.lower()
                
                word_pos =  clean_lemma + '_' + word[3]
                one_sentence_tagged += word_pos + ' '
        one_sentence_tagged = one_sentence_tagged.strip()
        sentences_tagged.append(one_sentence_tagged)
    return sentences_tagged

def get_pos_indexed_lemmatized_line(raw_text, ud_model):
    conllu = get_conllu_from_unite_line_text(raw_text, ud_model)
    conllu_text_map = get_conllu_text_map(conllu)
    #print(conllu_text_map)
    pos_indexed_lemm_list = assign_pos_index(conllu_text_map)
    lemm_pos_list = ' '.join(pos_indexed_lemm_list)
    return lemm_pos_list

def get_corpus_split_line(corpus_list, model):
    lemm_corpus_line = ''
    for text_index in tqdm(range(len(corpus_list))):
        raw_text = corpus_list[text_index]
        pos_text = get_pos_indexed_lemmatized_line(raw_text,model)
        lemm_corpus_line += pos_text + ' '
    lemm_corpus_line = lemm_corpus_line.split()
    return lemm_corpus_line

def unpos_split_line(posed_line_list):
    clear_list = []
    for posed_word in posed_line_list:
        clear_word = posed_word.split("_")[0]
        clear_list.append(clear_word)
    return clear_list

#stopwords = set(nltk.corpus.stopwords.words('russian'))
def rightTypes_bigram_with_pos_filter(ngram, stopwords, debug = False):
    if debug: print(ngram)
    for word in ngram:
        word_itself = word.split("_")[0]
        if word_itself in stopwords or word.isspace():
            if debug:print("stopword found")
            return False
    try:
        pos_1 = ngram[0].split("_")[1]
        pos_2 = ngram[1].split("_")[1]
    except:
        return False
    acceptable_types = ('ADJ', 'NOUN')
    if pos_1 in acceptable_types and pos_2 in acceptable_types:
        if debug:print("fltr ok")
        return True
    else:
        if debug:print("pos not ok")
        return False

def rightTypes_trigram_with_pos_filter(ngram, stopwords,debug = False):
    if debug: print(ngram)
    for word in ngram:
        word_itself = word.split("_")[0]
        if word_itself in stopwords or word.isspace():
            if debug:print("stopword found")
            return False
    try:
        pos_1 = ngram[0].split("_")[1]
        pos_3 = ngram[2].split("_")[1]
    except:
        return False
    acceptable_types = ('ADJ', 'NOUN')
    if pos_1 in acceptable_types and pos_3 in acceptable_types:
        if debug:print("fltr ok")
        return True
    else:
        if debug:print("pos not ok")
        return False

def get_pos_filtered_colloc_from_corpus_list(corpus_list, lang):
    if lang == "rus":
        model = Model('russian-syntagrus-ud-2.0-170801.udpipe')
        stopwords = set(nltk.corpus.stopwords.words('russian'))
    elif lang == "en":
        stopwords = set(nltk.corpus.stopwords.words('english'))
        model = Model('english-partut-ud-2.0-170801.udpipe')
    else:
        print("NO AVAILABLE LANGUAGE SPECIFIED. EXIT")
        return 0
    united_corpus_pos_tagged_list = get_corpus_split_line(corpus_list, model)
    lemm_corpus_split_list = unpos_split_line(united_corpus_pos_tagged_list)

    #POS and freq filtered
    bigramFreqTable, trigramFreqTable, quadgram_freq = get_freq_colloc(united_corpus_pos_tagged_list)
    filtered_bi = bigramFreqTable[bigramFreqTable.bigram.map(lambda x: rightTypes_bigram_with_pos_filter(x,stopwords))]
    filtered_tri = trigramFreqTable[trigramFreqTable.trigram.map(lambda x: rightTypes_trigram_with_pos_filter(x,stopwords))]

    #PMI filtered
    bigramPMITable, trigramPMITable, quadragramPMITable, bigramChiTable, trigramChiTable = get_pmi_and_chi_colloc(lemm_corpus_split_list)
    
    return bigramFreqTable, trigramFreqTable, quadgram_freq, filtered_bi, filtered_tri, bigramPMITable, trigramPMITable, quadragramPMITable, bigramChiTable, trigramChiTable

#FREQ PMI T-TEST CHII SQUARE APPROACH

#RUSSIAN pre-processing
def lemmatize_rus_text_get_split_list(raw_text, mystem_model):
    lemmas_ru = mystem_model.lemmatize(raw_text)
    clean_lemmas = ''
    for lemma in lemmas_ru:
        clean_lemma = ''
        for char in lemma:
            if char not in full_punctuation:
                clean_lemma += char
        clean_lemmas += clean_lemma + ' '
    clean_lemmas = clean_lemmas.strip()
    clean_lemmas_list = clean_lemmas.split()
    return clean_lemmas_list
def get_corpus_split_line_rus(corpus_list, model):
    lemm_corpus_line = []
    for text_index in tqdm(range(len(corpus_list))):
        raw_text = corpus_list[text_index]
        lemm_text = lemmatize_rus_text_get_split_list(raw_text,model)
        lemm_corpus_line.extend(lemm_text)
    return lemm_corpus_line

#ENGLISH pre-processing
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
        return ''

def get_lemm_list_en(text,model):
    clean_text = ''
    for char in text:
        if char in full_punctuation:
            clean_text += ' '
        else:
            clean_text += char.lower()

    final_lemm_list = []
    tkn = nltk.word_tokenize(clean_text)
    word_pos_list = nltk.pos_tag(tkn)
    for word_pos in word_pos_list:
        wordnet_pos = get_wordnet_pos(word_pos[1]) 
        if (wordnet_pos):
            lemma = model.lemmatize(word_pos[0], pos = wordnet_pos)
        else:
            lemma = model.lemmatize(word_pos[0])
        final_lemm_list.append(lemma)
    return final_lemm_list

def get_corpus_split_line_en(corpus_list, model):
    lemm_corpus_line = []
    for text_index in tqdm(range(len(corpus_list))):
        raw_text = corpus_list[text_index]
        lemm_text = get_lemm_list_en(raw_text,model)
        lemm_corpus_line.extend(lemm_text)
    return lemm_corpus_line

def get_colloc_from_corpus_list(corpus_list, lang):
    if lang == "rus":
        lemm_model = Mystem()
        corpus_split_line = get_corpus_split_line_rus(corpus_list, lemm_model)
    elif lang == "en":
        lemm_model = WordNetLemmatizer()
        corpus_split_line = get_corpus_split_line_en(corpus_list, lemm_model)
    else:
        print("NO AVAILABLE LANGUAGE SPECIFIED. EXIT")
        return 0
    bigramFreqTable, trigramFreqTable, quadgram_freq = get_freq_colloc(corpus_split_line)
    bigramPMITable, trigramPMITable, quadragramPMITable, bigramChiTable, trigramChiTable= get_pmi_and_chi_colloc(corpus_split_line)

    return bigramFreqTable, trigramFreqTable,quadgram_freq,  bigramPMITable, trigramPMITable, quadragramPMITable, bigramChiTable, trigramChiTable