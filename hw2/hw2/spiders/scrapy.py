import scrapy
from bs4 import BeautifulSoup

class ScrapySpider(scrapy.Spider):
    name = 'scrapy'
    start_urls = ['https://depart.moe.edu.tw/ED4500/Default.aspx']

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h2',class_='h4')

        print(title)
        
        rows = response.css('div.module_nems1_b ul li')

        for row in rows:
            post_date = row.css('div.h5 b::text').get()
            title = row.css('div.h5 a::text').get()

            yield { 
                "Post Date": post_date.strip(),
                "Title": title.strip()
            }
            print(post_date,title,)