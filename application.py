# -*- coding: utf-8 -*-
from flask import Flask,render_template,request,jsonify
from bs4 import BeautifulSoup as bs
from flask_cors import cross_origin,CORS
import requests
from urllib.request import urlopen as uReq
import logging,json
from pymongo import MongoClient


logging.basicConfig(filename='example.log', filemode='w', 
                    format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')


application = Flask(__name__)
app = application
WEBSITE_URL_1 = "https://www.flipkart.com"
comments_data = dict()
client = MongoClient("mongodb+srv://new_user31:VDWMCC7oPQMHMlSI@cluster0.swnzv.mongodb.net/?retryWrites=true&w=majority")

@app.route("/", methods=['GET'])
def index_page():
    return render_template("index.html")

@app.route("/review", methods=['GET', 'POST'])
def search_url():
    if request.method == 'POST':    
        try:
            test_db = client.search_product
            website = "www.flipkart.com"
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                logging.info("IP address logging is "+request.environ['REMOTE_ADDR'])
            else:
                logging.info("IP address logging when proxy setup "+request.environ['HTTP_X_FORWARDED_FOR']) # if behind a proxy
            website_url = f"https://{website}/"
            search_keywords = request.form['content'].strip().replace(" ","%20")
            if search_keywords == "":
                logging.debug("Empty string is requested")
                return "The review cannot be scraped for empty string" 
            website_url_search = website_url + "search?q=" + search_keywords
            logging.debug("URL POST request generated:  "+website_url_search)
            url_client = uReq(website_url_search)
            url_page_source = url_client.read()
            url_client.close()
            url_html = bs(url_page_source,'html.parser')
            big_boxes = url_html.find_all("div",{'class':'col-12-12'})
            logging.debug(len(big_boxes)) # length is 33
            # big boxes starts from 8
            # logging.debug(big_boxes[6].find_all('a', 'href'))
            first_page_sub_urls = []
            # finding urls from first page
            for box in url_html.find_all("div",{'class':'col-12-12'}):
                for b in box.find_all("a"):
                    temp_string = b.get('href')
                    if ".SEARCH" in temp_string:
                        first_page_sub_urls.append(temp_string)

            for i in range(len(first_page_sub_urls)):
                first_page_sub_urls[i] = WEBSITE_URL_1 + first_page_sub_urls[i]
            
            logging.debug(f"{first_page_sub_urls[9]} 9th url is the first product link")
            

            logging.debug(first_page_sub_urls)
            logging.debug("length of sub urls: " + str(len(first_page_sub_urls)))

            # grab review links
            # Sample: https://www.flipkart.com/micvir-back-cover-apple-iphone-11/product-reviews/itmd6651646281cf?pid=ACCG856NYKXDGZTK&lid=LSTACCG856NYKXDGZTKEEEVN2&marketplace=FLIPKART
            review_link = [] # link which contains reviews
            request_first_product = requests.get(first_page_sub_urls[0])
            request_first_product_html = bs(request_first_product.text,'html.parser')
            for div in request_first_product_html.find_all("div",{'class':'col-12-12'}):
                for href in div.find_all("a"):
                    temp_string = href.get('href')
                    if "product-reviews" in temp_string:
                        review_link.append(temp_string)
            logging.info(f"Product reviews link is: {review_link}")

            page_number_link = []
            count_page_numbers = 0
            request_page_numbers = requests.get(WEBSITE_URL_1 + review_link[0])
            request_page_numbers_html = bs(request_page_numbers.text,'html.parser')
            for div in request_page_numbers_html.find_all("div",{'class':'col-12-12'}):
                for href in div.find_all("a"):
                    temp_string = href.get('href')
                    if "&page=" in temp_string:
                        count_page_numbers+=1
                        page_number_link.append(WEBSITE_URL_1 + temp_string)
            logging.info(f"Product reviews Page numbers: {len(page_number_link)}")

            if len(page_number_link)==0:
                logging.debug("No reviews founds")
                return f"No reviews found for product {search_keywords}" 

            def loop_review(pages):
                # this function is for one page 
                count = 0
                for page in range(pages):
                    request_products = requests.get(page_number_link[page])
                    request_products_html = bs(request_products.text,'html.parser')
                    comment_box = request_products_html.find_all('div',{'class':'_1AtVbE col-12-12'}) # find all returns list
                    logging.info(f"Total number of comments in box: {len(comment_box)}")
                    for j in comment_box:
                        logging.debug("Inside comment_box")
                        try:
                            # logging.debug(j.div.div.div.div.find('div',{'class':'_3LWZlK _1BLPMq'}).text) #'class':'_3LWZlK _1BLPMq' customer rating 
                            try:
                                logging.debug(j.find_all('div',{'class':'_3LWZlK'})[0].text) # comment header 
                            except:
                                logging.debug("No rating")

                            try: 
                                logging.debug(j.div.div.find_all('div',{'class':''})[0].div.text) # customer_comment
                            except:
                                logging.debug("No comment")

                            try:
                                logging.debug(j.find('div',{'class':'_1LmwT9'}).span.text) # likes
                            except:
                                logging.debug("No likes")

                            try:
                                logging.debug(j.find('div',{'class':'_1LmwT9 pkR4jH'}).span.text) # dislikes
                            except:
                                logging.debug("No dislikes")

                            try:    
                                logging.debug(j.find('p',{'class':'_2sc7ZR _2V5EHH'}).text) # customer name
                            except:
                                logging.debug("No name")

                            logging.debug("\n")

                            index = count
                            temp_dict = dict()
                            
                            temp_dict["prod_name"]= search_keywords.replace("%20","-")
                            name = "name" #+ str(count)
                            try:
                                temp_dict[name]= j.find('p',{'class':'_2sc7ZR _2V5EHH'}).text
                            except:
                                temp_dict[name]="No name"

                            customer_rating = "customer_rating" #+ str(count)
                            try:
                                temp_dict[customer_rating]= j.find_all('div',{'class':'_3LWZlK'})[0].text
                                temp_dict[customer_rating] = temp_dict[customer_rating]
                            except:
                                temp_dict[customer_rating] = "No rating"

                            comment_header = "comment_header" #+ str(count)
                            try:
                                temp_dict[comment_header]= str(j.div.div.div.div.p.text)
                                temp_dict[comment_header] = temp_dict[comment_header].replace('“','"').replace('”','"')
                            except:
                                temp_dict[comment_header] = "No header"

                            customer_comment = "customer_comment" #+ str(count)
                            try:
                                temp_dict[customer_comment]= str(j.div.div.find_all('div',{'class':''})[0].div.text)
                                temp_dict[customer_comment] = temp_dict[customer_comment].replace('“','"').replace('”','"')
                            except:
                                temp_dict[customer_comment] = "No comment"

                            likes = "likes" #+ str(count)
                            try:
                                temp_dict[likes]= j.find('div',{'class':'_1LmwT9'}).span.text
                            except:
                                temp_dict[likes]= "No likes"

                            dislikes = "dislikes" #+ str(count)
                            try:
                                temp_dict[dislikes]= j.find('div',{'class':'_1LmwT9 pkR4jH'}).span.text
                            except:
                                temp_dict[dislikes] = "No dislikes"

                            try:    
                                comments_data[index] = temp_dict
                            except:
                                # comments_data[index] = {"name":"no name",        
                                #                         "customer_rating": "No rating",
                                #                         "comment_header": "No header",
                                #                         "customer_comment": "No comment",
                                #                         "likes": "No likes",
                                #                         "dislikes": "No dislikes"}
                                logging.debug("Error during indexing")
                            

                            test_db["customer_review"].insert_one(temp_dict)

                        except AttributeError:
                            logging.error("error")
                        count +=1
                
                # logging.debug(json.dumps(comments_data))
            try:
                loop_review(10) # 10 pages data scraped
            except Exception as e:
                logging.debug("Review page not found due to: ",e)
            with open(f'{search_keywords.replace("%20","-")}.csv', 'w') as f:
                for key in comments_data.keys():
                    f.write("%s,%s\n"%(key,comments_data[key]))
            return render_template("results.html",reviews = comments_data)
        except Exception as e:
            logging.debug("Caught the exception: ",e)
            return f"The review cannot be scraped for product {search_keywords}"
    else:
        return render_template("index.html")        

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)