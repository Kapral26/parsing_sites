# -*- coding: utf-8 -*-
import json
import logging
import sys

import requests
from bs4 import BeautifulSoup

logging.basicConfig(filename="parsing_taxi.log",
					format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
					level=logging.INFO)
sys.sterr = sys.stdin = logging


class Ya_Parser:
	def __init__(self):
		self.main_url = u'https://yandextaxi.top/partner/'
		self.taxi_of_the_city = list()

	def find_all_city(self):
		req_city = requests.get(self.main_url)
		bs_city = BeautifulSoup(req_city.text, "html.parser")
		list_city_li = bs_city.findAll('li', class_='cat-item')
		self.taxi_of_the_city = [{'city_name': x.find('a').text, 'link': x.find('a').get('href')} for x in list_city_li]
		for city in self.taxi_of_the_city:
			logging.info(f'Собираем данные по городу:{city["city_name"]}')
			city['firms'] = self.collect_taxi_firm(city['link'])
			logging.info(f'Данные собраны, количество фирм найдено: {city["firms"].__len__()}')

	def collect_taxi_firm(self, url):
		req_firm = requests.get(url)
		bs_firm = BeautifulSoup(req_firm.text, "html.parser")
		list_firm_data = bs_firm.findAll('a', class_='category-ttl')
		list_firm = list()
		for firm in list_firm_data:
			firm_data = self.collect_data(firm.get('href'))
			list_firm.append(firm_data)
		return list_firm

	def collect_data(self, url):
		req_firm_data = requests.get(url)
		bs_firm_data = BeautifulSoup(req_firm_data.text, "html.parser")
		table = bs_firm_data.findAll('td')
		keys = [x.text for x in table[::2]]
		value = [x.text for x in table[1::2]]
		return dict(zip(keys, value))

	def write_json(self):
		"""
		Пишем данные в json
		"""
		logging.info('start write json')

		with open("taxi_file.json", "w", encoding='utf8') as write_file:
			json.dump(self.taxi_of_the_city, write_file, ensure_ascii=False)
		logging.info('end write json')

	def run(self):
		logging.info('start')
		self.find_all_city()
		self.write_json()
		logging.info('end')


if __name__ == '__main__':
	Ya_Parser().run()
