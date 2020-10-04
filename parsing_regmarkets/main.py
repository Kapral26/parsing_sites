# -*- coding: utf-8 -*-
import json
import logging
import re

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

logging.basicConfig(filename="building_material.log",
					format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
					level=logging.INFO)


class ParsingHeads:
	def __init__(self):
		self.main_link = 'https://moskva.regmarkets.ru/category/'
		self.main_data = list()

	def collcet_first_level(self):
		response = requests.get(self.main_link)
		bs_obj = BeautifulSoup(response.text, "html.parser")
		sections = bs_obj.findAll(class_="catalogLinksBox")
		logging.info(f'Найдно разделов: {sections.__len__()}')
		for section in sections:
			section_data = dict()
			head = section.findAll('div', class_='catalogLinksBoxTitle')[0].text
			head = re.findall('[А-я]+', head)[0]
			logging.info(f'1: Раздел: {head}')
			section_data[head] = self.collect_second_level(section)
			logging.info(f'Раздел: {head} - Done')
			self.main_data.append(section_data)

	def collect_second_level(self, bs_f_lvl):
		section_2_lvl_data = dict()
		list_urls = bs_f_lvl.findAll('a')
		logging.info(f'В разделе найдно секций: {list_urls.__len__()}')
		for url_sec in list_urls:
			section_2_lvl_data[url_sec.text] = dict()
			url = f'https://moskva.regmarkets.ru/{url_sec.get("href")}'
			prod_req = requests.get(url)
			bs_obj = BeautifulSoup(prod_req.text, "html.parser")
			products = bs_obj.findAll(class_='categoriesInnerListBoxTitle')
			logging.info(f'2: Секция: {url_sec.text}')
			for prod in products:
				prod_name = prod.text
				logging.info(f'3: Раздел в секции: {prod_name}')
				section_2_lvl_data[url_sec.text][prod_name] = self.collect_third_level(
						prod.find('a').get('href'))
			logging.info(f'Секция: {url_sec.text} - Done')
		return section_2_lvl_data

	def collect_third_level(self, url):
		url = f'https:{url}'
		prod_req = requests.get(url)
		bs_prod = BeautifulSoup(prod_req.text, "html.parser")
		try:
			list_prods = bs_prod.findAll('div', class_='sideNavList')[0].findAll('li')[1:]
		except IndexError:
			list_prods = list()
		logging.info(f'В сеции разделов: {list_prods.__len__()}')
		return [x.text for x in list_prods]

	def write_excel(self):
		"""
		Пишем данные в xlsx
		"""
		logging.info('start write xlsx')


		with open("data_file.json", "w", encoding='utf8') as write_file:
			json.dump(self.main_data, write_file)
		# wb = Workbook()
		# ws = wb.active
		# for key1 in self.main_data:
		# 	for key2 in key1.keys():
		# 		for key3 in key1[key2].keys():
		# 			for key4 in key1[key2][key3].keys():
		# 				for key5 in key1[key2][key3][key4]:
		# 					row = [key2, key3, key4, key5]
		# 					ws.append(row)
		# wb.save('build.xlsx')
		logging.info('end write xlsx')

	def run(self):
		logging.info('start')
		self.collcet_first_level()
		self.write_excel()
		logging.info('end')


if __name__ == '__main__':
	ParsingHeads().run()
