from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future 
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
import time
import requests
import os
from tqdm.auto import tqdm
import random
from bs4 import BeautifulSoup as bs
import json

from lxml.html import fromstring
import requests
import ipaddress
from itertools import cycle
import traceback

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--links_list")
parser.add_argument("-f", "--from_index")
parser.add_argument("-t", "--to_index")
args = parser.parse_args()


with open(args.links_list,"r") as f:
    links_list = json.load(f)


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
                # print("restcit_eba")
                #raise Exception('Restiction_limit!!!!!!!!!!!!!!')
                return True
    return False

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    proxy_pool = cycle(proxies)

    for i in range(1,11):
        #Get a proxy from the pool
        proxy = next(proxy_pool)
        print("Request #%d"%i)
        try:
            response = requests.get('https://httpbin.org/ip',proxies={"http": proxy, "https": proxy})
            print(response.json())
            return {"http": proxy, "https": proxy}
        except:
            #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
            #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 
            print("Skipping. Connnection error")
    return None

def save_result(folder, url, response):
    save_dir = os.path.join(folder ,url.split("/")[-1] + ".xls")
    #print("saved at ",save_dir)
    file = open(save_dir, "wb")
    file.write(response.content)
    file.close()


def only_send_request_func(url):
    global proxy
    #print("here")
    land_dict = {"русский":"ru","французский":"fr", "английский":"en"}
    lang_pair = url.split("/")[-2]
    from_lang = lang_pair.split("-")[0]
    to_lang = lang_pair.split("-")[1]
    save_loc_base = "/Users/nigula/LL/adjust_unigr_dict/lookup/reverso_" + land_dict[from_lang] + "_" + land_dict[to_lang]
    handled_words_list = []
    for word in os.listdir(save_loc_base):
        handled_words_list.append(word.split(".")[0])
    handled_words_set = set(handled_words_list)   
    word_to_be_requested = url.split("/")[-1]
    #print("extract word")
    if word_to_be_requested not in handled_words_set:
        #print("to be handled")
        login = {'inUserName': 'n.babakov@lingualeo.com', 'inUserPass': '33vec33'}
        header_main = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        response = requests.get(url, headers=header_main, data = login)
        response.encoding = 'utf-8' 
        soup = bs(response.text, 'html.parser') 
        is_resticted = check_restiction(soup)
        if is_resticted == True:#use previous proxy
            # print("restriction, going to use", proxy)
            response = requests.get(url, headers=header_main, data = login, proxies = proxy)
            response.encoding = 'utf-8' 
            soup = bs(response.text, 'html.parser') 
            is_resticted = check_restiction(soup)
            if is_resticted == True:#use new proxy
                print("previpus_proxy_failed, generate_new")
                proxy = get_proxies()
                if proxy == None:
                    time.sleep(3)
                    response = requests.get(url, headers=header_main, data = login)
                else:
                    response = requests.get(url, headers=header_main, data = login, proxies = proxy)
                response.encoding = 'utf-8' 
                soup = bs(response.text, 'html.parser') 
                is_resticted = check_restiction(soup)
                if is_resticted == False:
                    save_result(save_loc_base,url, response )
                # save_dir = os.path.join(save_loc_base ,url.split("/")[-1] + ".xls")
                # file = open(save_dir, "wb")
                # file.write(response.content)
                # file.close()
                
                # print("restiction. sleep for 20 sec") 
                # time.sleep(random.uniform(20, 30))
            else:
                time.sleep(3)
                save_result(save_loc_base,url, response )
        # save_dir = os.path.join(save_loc_base ,url.split("/")[-1] + ".xls")
        # # print("saved at ",save_dir)
        # file = open(save_dir, "wb")
        # file.write(response.content)
        # file.close()
        else:
            save_result(save_loc_base,url, response )
                # time.sleep(random.uniform(0.1, 0.9))
    # else:
    #     #print(word_to_be_requested, "already_handles")
    #     pass

list_to_be_processed = links_list
# from_ind = int(args.from_index)#
#from_ind = 1167 + 4829 + 23000 + 2456 + 3000 + 2749 + 5943
from_ind = 90000 + 2520
to_ind = len(list_to_be_processed)
proxy = get_proxies()
with ProcessPoolExecutor(max_workers=2) as executor:
    start = time.time()
    futures = [ executor.submit(only_send_request_func, url) for url in list_to_be_processed[from_ind:to_ind]]
    results = []
    for result in tqdm(as_completed(futures), total=int(to_ind-from_ind)):
        results.append(result)
    end = time.time()
    print("Time Taken: {:.6f}s".format(end-start))