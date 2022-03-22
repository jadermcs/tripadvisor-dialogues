import json
import scrapy


class ThreadSpider(scrapy.Spider):
    name = "thread"
    criteria = 20
    start_urls = [
        'https://www.tripadvisor.com/ShowForum-g186338-i17-London_England.html'
    ]

    def thread_parse(self, response):
        replies = []
        for index, post in enumerate(response.css('div.postBody')):
            text = []
            entities = []
            for paragraph in post.css('p'):
                sentence = paragraph.css('::text').getall()
                if sentence is not None:
                    text += [s for s in sentence if not s.startswith("(ta")]
                    entities += paragraph.css('a.internal::text').getall()
            if len(text) > 1000:
                if index == 0: return
                continue
            replies.append({'utterance': ' '.join(text), 'entities': entities})
        yield {
            'url': response.url,
            'domain': response.url.split('-')[-1].rstrip('.html'),
            'intent': response.css('h1#HEADING::text').get().strip(),
            'utterances': replies
        }

    def parse(self, response):
        page = response.url.split("/")[-1]
        filename = 'data/page-{}.jl'.format(page)
        fileout = open(filename, 'w')
        for thread in response.xpath('//*[@id="SHOW_FORUMS_TABLE"]/tr'):
            item = thread.css('td b a')
            url = item.css('::attr(href)').get()
            if url is not None:
                count = thread.css('td.reply.rowentry::text').get()
                count = int(count.strip().replace(',',''))
                name = item.css('::text').get()
                fileout.write(json.dumps({
                        'name': name.strip(),
                        'url': url,
                        'replies': count,
                }))
                fileout.write('\n')
                if count <= self.criteria:
                    yield response.follow(url, callback=self.thread_parse)
        fileout.close()
        next_page = response.css('a.guiArw.sprite-pageNext::attr(href)').get()
        if next_page is not None:
            self.log('Crawling page {}'.format(next_page))
            yield response.follow(next_page, callback=self.parse)