# -*- coding: utf-8 -*-
import scrapy, time, json
from scrapy.utils.misc import load_object
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from Tencent.items import TencentItem
import logging
import re


logger = logging.getLogger(__name__)


class TencentSpider(scrapy.Spider):
    name = 'tencent'
    allowed_domains = ['tencent.com']
    base_url = "https://careers.tencent.com/search.html?index={page}"

    custom_settings = {
        'COOKIES_ENABLED': False,
        'LOG_LEVEL': 'INFO',
        'DOWNLOADER_MIDDLEWARES': {
            'common.middlewares.FireFoxMiddleware': 90,
        },
        'ITEM_PIPELINES': {
        'Tencent.pipelines.TencentMysqlPipeline': 300,
        }
    }


    def start_requests(self):
        page = 1
        url = self.base_url.format(page=page)
        yield scrapy.Request(url, dont_filter=True, meta={'page': page})

    def parse(self, response):
        page = response.meta.get('page', "1")
        logger.info("开始爬取第【%s】页" % page)
        recruits = response.xpath('//div[@class="recruit-list"]')
        for recruit in recruits:
            item = TencentItem()
            recruit_post_mame  = recruit.xpath('./a/h4[@class="recruit-title"]/text()').get()

            bg_name = recruit.xpath('./a/p[@class="recruit-tips"]/span/text()').get()
            country_location_name = recruit.xpath('./a/p[@class="recruit-tips"]/span[2]/text()').get()
            category_name = recruit.xpath('./a/p[@class="recruit-tips"]/span[3]/text()').get()
            last_update_time = recruit.xpath('./a/p[@class="recruit-tips"]/span[last()]/text()').get()
            responsibility = recruit.xpath('./a/p[@class="recruit-text"]/text()').get()
            item['RecruitPostName'] = recruit_post_mame.strip() if recruit_post_mame else ''
            item['BGName'] = bg_name
            item['CategoryName'] = category_name
            item['Responsibility'] = responsibility.strip() if responsibility else ''
            if country_location_name:
                res = country_location_name.split(',')
                if len(res) == 2:
                    item['LocationName'] = res[0]
                    item['CountryName'] = res[1]
            if last_update_time:
                pattern = re.compile(r'(\d{4})\w(\d{1,2})\w(\d{1,2})')
                result = pattern.search(last_update_time)
                if result and len(result.groups()) == 3:
                    item['LastUpdateTime'] = '-'.join([x for x in result.groups()])
            yield item
        page = page + 1
        url = self.base_url.format(page=page)
        yield scrapy.Request(url, callback=self.parse, meta={'page': page})





