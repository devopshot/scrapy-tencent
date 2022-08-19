from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from scrapy.http import HtmlResponse
from scrapy import signals
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import platform


class FireFoxMiddleware(object):

    def __init__(self):
        options = Options()
        options.add_argument('-headless')
        if platform.system() == 'Linux':
            server = Service(executable_path='/usr/local/bin/geckodriver')
        else:
            server = Service()
        self.driver = webdriver.Firefox(options=options, service=server)
        self.driver.delete_all_cookies()
        self.wait = WebDriverWait(self.driver, 10)

    @classmethod
    def from_crawler(cls, crawler):
        o = cls()
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_closed(self, spider):
        self.driver.quit()
        spider.logger.info('%s 爬虫结束' % spider.name)

    def process_request(self, request, spider):

        if spider.name == 'tencent':
            try:
                spider.logger.info("开始启动firefox...")
                spider.logger.info("URL 为 %s" % request.url)
                self.driver.get(request.url)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.recruit-list')))
            except TimeoutException:
                origin_code = None
                status = 500
            else:
                origin_code = self.driver.page_source
                status = 200

            return HtmlResponse(url=request.url, request=request, body=origin_code, encoding='utf-8',
                                    status=status)



