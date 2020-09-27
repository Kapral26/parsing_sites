# -*- coding: utf-8 -*-
import re

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(filename="parsing_watchs.log", format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)
logging.StreamHandler()

class ParsingWatch:
	def __init__(self):
		self.main_url = None
		self.urls = {'Diesel_m': 'muzhskie-chasy/?page={0}&q=Бренд-Diesel',
					 'Guess_f': 'zhenskie-chasy/?page={0}&q=Бренд-Guess',
					 'Guess_m': 'muzhskie-chasy/?page={0}&q=Бренд-Guess',
					 'Michael_f': 'zhenskie-chasy/?page={0}&q=Бренд-Michael'}
		self.main_list = dict()

	def find_count_page(self, url):
		response = requests.get(url.format(1))  # берем первцю страниуц
		soup_obj = BeautifulSoup(response.text, "html.parser")
		page_nums = soup_obj.findAll('ul', class_='col-md-12 text-center')
		return max(re.findall('[0-9]', page_nums[0].text))

	def collect_html_data(self):
		result = list()

		for key in self.urls.keys():
			url = f"https://www.sevenwatches.ru/chasy/{self.urls[key]}"
			count_pages = self.find_count_page(url)
			result.append({'count_pages': int(count_pages), 'url': url, 'name_mass': key})
			logging.info(f'pages: {key}, count_pages: {count_pages}')
		return result

	def goes_to_pages(self, list_pasing_data):
		count_pages = list_pasing_data.get('count_pages') + 1
		url_page = list_pasing_data.get('url')
		name_mass = list_pasing_data.get('name_mass')

		logging.info(f'{name_mass}')

		for n_page in range(1, count_pages):
			logging.info(f'work with page: {n_page}/{list_pasing_data.get("count_pages")}')
			response_page = requests.get(url_page.format(n_page))
			page_soup =  BeautifulSoup(response_page.text, "html.parser")
			self.find_product(page_soup, name_mass)
		logging.info('Done')

	def find_product(self, page_soup, name_mass):
		watchs = page_soup.findAll('a', class_='product-thumbnail')
		for watch in watchs:
			page_watch = requests.get(watch.get('href'))
			soup_watch = BeautifulSoup(page_watch.text, "html.parser")
			part1 = soup_watch.findAll('div', class_='product-custom-features')
			watch_info = {x.split('\n')[0].replace(':', ''): x.split('\n')[1] for x in
						  part1[0].text.strip('\n\n\n').split('\n\n\n')}

			part2 = soup_watch.findAll('div', class_=['product-feature-name', 'product-feature-value'])

			part2 = {x.text.split(': ')[0]: x.text.split(': ')[1] for x in part2[::2]}

			watch_info = {**watch_info, **part2}

			self.main_list[name_mass].append(watch_info)


	def run(self):
		logging.info('Start')
		list_data_pages = self.collect_html_data()

		for pages in list_data_pages:
			self.goes_to_pages(pages)
		logging.info('End')



if __name__ == '__main__':
	ParsingWatch().run()
