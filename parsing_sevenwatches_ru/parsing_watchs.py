# -*- coding: utf-8 -*-
import logging
import os
import re
import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas import ExcelWriter

logging.basicConfig(filename="parsing_watchs.log",
					format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
					level=logging.INFO)
sys.sterr = sys.stdin = logging


class ParsingWatch:
	def __init__(self):
		self.main_url = None
		self.urls = {'Diesel_m': 'muzhskie-chasy/?page={0}&q=Бренд-Diesel',
					 'Guess_f': 'zhenskie-chasy/?page={0}&q=Бренд-Guess',
					 'Guess_m': 'muzhskie-chasy/?page={0}&q=Бренд-Guess',
					 'Michael_f': 'zhenskie-chasy/?page={0}&q=Бренд-Michael'}
		self.main_list = {x: list() for x in self.urls.keys()}

	def find_count_page(self, url):
		"""
		Ищем на первой странице. всего количество страниц по данному товару
		:param url: url первой страницы
		:return: последний порядковый номер страницы товара
		"""
		response = requests.get(url.format(1))  # берем первцю страниуц
		soup_obj = BeautifulSoup(response.text, "html.parser")
		page_nums = soup_obj.findAll('ul', class_='col-md-12 text-center')
		return max(re.findall('[0-9]', page_nums[0].text))

	def collect_html_data(self):
		"""
		Сбор информации для дальнейшейго парсинга
		:return: dict(), 'count_pages': количество всего листов товара 'url': ссылка на страницу, 'name_mass': что за товар
		"""
		result = list()

		for key in self.urls.keys():
			url = f"https://www.sevenwatches.ru/chasy/{self.urls[key]}"
			count_pages = self.find_count_page(url)
			result.append({'count_pages': int(count_pages), 'url': url, 'name_mass': key})
			logging.info(f'pages: {key}, count_pages: {count_pages}')
		return result

	def goes_to_pages(self, list_pasing_data):
		"""
		Парсим непосредственно страницу с товарами
		:param list_pasing_data: collect_html_data()
		"""
		count_pages = list_pasing_data.get('count_pages') + 1
		url_page = list_pasing_data.get('url')
		name_mass = list_pasing_data.get('name_mass')

		logging.info(f'{name_mass}')

		for n_page in range(1, count_pages):
			logging.info(f'work with page: {n_page}/{list_pasing_data.get("count_pages")}')
			response_page = requests.get(url_page.format(n_page))
			page_soup = BeautifulSoup(response_page.text, "html.parser")
			self.collect_product_data(page_soup, name_mass)
		logging.info('Done')

	def collect_product_data(self, page_soup, name_mass):
		"""
		Сбор данных о товарах на странице
		:param page_soup: bs4 объект всех товаров
		:param name_mass: наименование товара
		:return: Наполняем словарь self.main_list данными для каждого товара списком данных
		"""

		def collect_image(soup, name_mass, watch_name):
			"""
			Собор картинок товара
			:param soup: bs4 объект страницы товара
			:param watch_name: название товара
			"""

			# создаём каталог для хранения изображений
			dir_pic_path = os.path.join(os.path.dirname(__file__), 'imgs', f'{name_mass}_' f'{watch_name}').replace(' ', '_')

			if not os.path.exists(dir_pic_path):
				os.makedirs(dir_pic_path)

			# собираем все ссылки на картинки, у которых есть параметр data-large-url
			pictures = soup.findAll('img', title=watch_name)
			links_pics = list()
			for pic in pictures:
				if 'data-large-url' in pic.attrs.keys():
					links_pics.append(pic.get('src'))

			# скачиваем картинки в ранее созданный каталог
			for link_pic in set(links_pics):
				name_pic = link_pic.replace('https://www.sevenwatches.ru/', '').replace('/', '_')

				p = requests.get(link_pic)
				new_img_path = os.path.normpath(os.path.join(dir_pic_path, name_pic))
				with open(new_img_path, "wb") as out:
					out.write(p.content)

			return f'imgs/{watch_name}'

		watchs = page_soup.findAll('a', class_='product-thumbnail')  # ссылки на все товары на странице
		for watch in watchs:
			page_watch = requests.get(watch.get('href'))
			soup_watch = BeautifulSoup(page_watch.text, "html.parser")

			watch_name = soup_watch.find(class_='product_name_md').text
			try:
				price = soup_watch.find(class_='regular-price').text
			except:
				price = soup_watch.find(class_='price').text

			keys = soup_watch.findAll('span', class_=['custom-feature-name', 'custom-feature-value'])[::2]
			values = soup_watch.findAll('span', class_=['custom-feature-name', 'custom-feature-value'])[1::2]
			watch_info = dict(zip([x.text for x in keys], [x.text for x in values]))

			img_path = collect_image(soup_watch, name_mass, watch_name)
			watch_info['Картинки'] = img_path

			specifications = soup_watch.findAll('div', class_=['product-feature-name', 'product-feature-value'])

			specifications = {x.text.split(': ')[0]: x.text.split(': ')[1] for x in specifications[::2]}

			watch_info = {**watch_info, **specifications}
			watch_info['Наименование продукта'] = watch_name
			watch_info['Цена'] = price

			self.main_list[name_mass].append(watch_info)

	def write_excel(self):
		"""
		Пишем данные в xlsx
		"""
		logging.info('start write xlsx')
		for key in self.main_list.keys():
			logging.info(f'write sheet: {key}')
			df = pd.DataFrame(self.main_list[key])
			writer = ExcelWriter('../watchs.xlsx')
			df.to_excel(writer, 'main_sheet', index=False)
			writer.save()
		logging.info('end write xlsx')

	def run(self):
		logging.info('Start')
		list_data_pages = self.collect_html_data()

		for pages in list_data_pages:
			self.goes_to_pages(pages)
		logging.info('End')

		self.write_excel()


if __name__ == '__main__':
	ParsingWatch().run()
