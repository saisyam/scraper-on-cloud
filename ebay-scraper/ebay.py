import sys
import json
import requests
from bs4 import BeautifulSoup
import unicodedata
from headers import *


def scrape_ebay_product(url):
    r = requests.get(url, headers=get_headers())
    soup = BeautifulSoup(r.text, "html5lib")
    msgpanel = soup.find('div', {'id','msgPanel'})
    if msgpanel is not None:
        if "listing was ended" in msgpanel.get_text().strip():
            return
    cpanel = soup.find("div", {'id':'CenterPanel'})
    container = soup.find("div", {'id': 'vi-layout-container'})
    if cpanel is not None:
        return json.dumps(scrape_product_type_2(soup, url))
    elif container is not None:
        return json.dumps(scrape_product_type_3(soup, url))
    else:
        return json.dumps(scrape_product_type_1(soup, url))

def scrape_product_type_1(soup, url):
    title= soup.find("div", {'id':'mainContent'}).find("h1", {'class':'product-title'}).get_text().replace('Details about','').strip()
    centerpanel = soup.find('div', {'id':'center-panel'})
    img_wrapper = centerpanel.find('div', {'class':'item-image-wrapper'})
    ebay_id = img_wrapper['data-listingid']
    pic_panel = img_wrapper.find('div', {'class':'hero-picture-panel'}).find('div',{'class':'thumbPicturePanel'})
    imgs = pic_panel.find_all("figure")
    img_urls = []
    for img in imgs:
        img_urls.append(img.find('img')['src'].replace("s-l64","s-l640"))
    item_desc = centerpanel.find("div", {'class':'item-desc'})
    price = item_desc.find("div", {'class':'display-price'}).get_text()
    shipping = item_desc.find("span", {'class':'logistics-cost'}).get_text().replace("+",'').replace('Shipping','').strip()
    product_desc = soup.find("div", {'class':'btf-content'}).find("div", {'id':'ProductDetails'}).find('section',{'class':'product-spectification'})
    rows = product_desc.find_all('div',{'class':'spec-row'})
    metadata = {}
    metadata['price'] = price
    metadata['shipping'] = shipping
    for row in rows:
        items = row.find("ul").find_all("li")
        for item in items:
            divs = item.find_all("div")
            if len(divs) > 0:
                metadata[item.find("div",{'class':'s-name'}).get_text()] =  item.find("div",{'class':'s-value'}).get_text()
            else:
                metadata[row.find("h2").get_text()] = item.get_text()
    return {
        'title': title,
        'ebay_id': ebay_id,
        'images': img_urls,
        'metadata': metadata,
        'url': url
    }

def scrape_product_type_2(soup, url):
    left_panel = soup.find("div", {'id': 'LeftSummaryPanel'})
    title = left_panel.find("div",{'class':'vi-swc-lsp'}).find("h1", {'id':'itemTitle'}).get_text()
    title = unicodedata.normalize("NFKD", title).replace('Details about','').strip()
    mcontent = soup.find("div", {'id':'mainContent'})
    price_span = mcontent.find("span", {'itemprop':'price'})
    price = price_span.get_text().strip()
    shipping_id = mcontent.find("span", {'id':'fshippingCost'})
    shipping = ""
    if shipping_id is not None: # sometime shipping need to be calculated
        shipping = shipping_id.get_text().strip()
    desc_section = soup.find("div", {'id':'BottomPanel'}).find("div", {'id':'viTabs_0_is'}).find("div",{'class':'section'})
    metadata = {}
    metadata['price'] = price
    metadata['shipping'] = shipping
    tables = desc_section.find_all('table')
    desc_table = None
    if len(tables) > 1:
        seller_desc_table = desc_section.find('table',{'id':'itmSellerDesc'})
        if seller_desc_table is not None:
            rows = seller_desc_table.find_all("tr")
            for row in rows:
                key = row.find("th").get_text().strip().replace(":",'')
                value = row.find("td").get_text().strip().replace("\t",'').replace("\n",'')
                metadata[key] = value
        desc_table = tables[1]
    else:
        desc_table = desc_section.find('table')
        
    rows = desc_table.find_all("tr")
        
    for row in rows:
        td = row.find_all("td")
        if len(td) > 0:
            key = td[0].get_text().strip().replace(":",'')
            spans = td[1].find_all('span')
            if len(spans) > 0:
                value = spans[0].get_text().strip().replace("\t",'').replace("\n",'')
            else:
                value = td[1].get_text().strip().replace("\t",'').replace("\n",'')
            metadata[key] = value
            if len(td) > 2:
                key = td[2].get_text().strip().replace(":",'')
                value = td[3].get_text().strip()
                metadata[key] = value
        
    img_div = soup.find("div", {'id':'vi_main_img_fs'})
    img_urls = []
    if img_div is not None:
        images = img_div.find("ul").find_all("li")
        for img in images:
            img_urls.append(img.find("img")['src'].replace('s-l64', 's-l1600'))
    else:
        img_div = soup.find("div", {'id':'mainImgHldr'})
        img_url = img_div.find("img", {'id':'icImg'})['src']
        img_urls.append(img_url)
        
            
    ebay_id = soup.find("div", {'id':'descItemNumber'}).get_text()
    return {
        'title': title,
        'ebay_id': ebay_id,
        'images': img_urls,
        'metadata': metadata,
        'url': url
    }

def scrape_product_type_3(soup, url):
    container = soup.find("div", {'id': 'vi-layout-container'})
    center_panel = container.find("div", {'name':'wrapper-centerpanel'})
    left_block = center_panel.find('div', {'class':'vi-wireframe__middle-block--to-left'})
    title = left_block.find('h1',{'class':'vi-title__main'}).get_text().strip()
    price = left_block.find('span', {'class':'main-price-with-shipping'}).get_text().strip()
    shipping = left_block.find('span', {'class':'logistics-cost'}).get_text().replace('+', '').replace('Shipping','').strip()
    container1 = container.find("div",{'id':'vi-frag-btfcontainer'})
    meta_container = container1.find('div',{'class':'app-itemspecifics-mobile-wrapper'})
    items = meta_container.find_all('dl')
    metadata = {}
    for item in items:
        key = item.find('dt').get_text().strip()
        value = item.find('dd').get_text().strip()
        metadata[key] = value
    pic_panel = container.find('div',{'class':'vi-wireframe__left-block'}).find('div',{'class':'thumbPicturePanel'})
    imgs = pic_panel.find_all("figure")
    img_urls = []
    for img in imgs:
        img_urls.append(img.find('img')['src'].replace("s-l64","s-l1600"))
    return {
        'title': title,
        #'ebay_id': ebay_id,
        'images': img_urls,
        'metadata': metadata,
        'url': url
    }
