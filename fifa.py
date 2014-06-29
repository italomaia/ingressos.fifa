# coding:utf-8

from urllib import urlopen
import argparse
import json
import re
import subprocess
from time import sleep


# returns json (same used by ingresso site)
uri_available_games = 'https://fwctickets.fifa.com/TopsAkaCalls/Calls.aspx/getBasicData?l=pt&c=BRA'
date_c = re.compile('(\d{4})(\d{2})(\d{2})')
mp3 = 'eh_tetra.mp3'

class Product(object):
    def __init__(self, prd, codes):
        self.id = prd['ProductId']
        self.description = prd['ProductPublicName']
        self.date = date_c.match(prd['MatchDate']).groups()
        self.stadium = self.get_stadium(codes)

    def __repr__(self):
        date = list(self.date)
        date.reverse()
        date_str = u'%s/%s/%s' % tuple(date)

        return ('ID: %s - %s - %s no %s' % (self.id, date_str, self.description, self.stadium['StadiumName'])).encode('utf-8')

    def get_product(self, codes):
        for prd in codes['PRODUCTS']:
            if prd['ProductId'] == self.id:
                return prd

    def get_category(self, codes):
        prd = self.get_product(codes)

    def get_prices(self, codes):
        prd = self.get_product(codes)
        prices = []
        
        for price in codes['PRODUCTPRICES']:
            if price['PRPProductId'] == self.id:
                prices.append(price)

        return prices

    def get_stadium(self, codes):
        prd = self.get_product(codes)
        stadium_id = prd['MatchStadium']
        
        for venue in codes['VENUES']:
            if venue['StadiumId'] == stadium_id:
                return venue

    def is_closed(self, codes):
        return self.get_product(codes)['closed'] == 'Y'


def consult():
    resp = urlopen(uri_available_games).read()
    json_resp = json.loads(resp)
    data = json_resp['d']['data']
    json_data = json.loads(data)
    codes = json_data['BasicCodes']
    return codes


def get_parser():
    parser = argparse.ArgumentParser(description='Parser de ingressos do script fifa')
    parser.add_argument('-J', '--jogos', dest='games', help='Id do jogo desejado', nargs='+')
    parser.add_argument('-a', '--abertos', dest='all_open', action='store_true', help='Exibir jogos que ainda não aconteceram')
    parser.add_argument('-t', '--todos', dest='all', action='store_true', help='Exibir todos os jogos')
    parser.add_argument('-c', '--cabecalho', dest='header', action='store_true', help='Imprime cabeçalhos')
    parser.add_argument('-v', '--vendendo', dest='selling', action='store_true', help='Exibir jogos com ingresso à venda')
    parser.add_argument('-l', '--loop', dest='loop', action='store_true', help='Deixa o script rodando indefinidamente')
    return parser


def full_product_list(codes):
    product_list = []
    for prd in codes['PRODUCTS']:
        product = Product(prd, codes)
        product_list.append(product)
    return product_list


def open_product_list(codes):
    return filter(lambda i: not i.is_closed(codes), full_product_list(codes))


def show_selling(codes, games):
    product_list = open_product_list(codes)

    if games:
        product_list = filter(lambda i: i.id in games, product_list)

    for product in open_product_list(codes):
        prices = product.get_prices(codes)
        
        if any(map(lambda i: int(i['Quantity']) > 0, prices)):
            print product, 'tem ingresso!'
            
            try:
                subprocess.call(['mpg123', mp3], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                print('mpg123 não foi encontrado. Sem sonzinho procê!')


def main():
    parser = get_parser()
    args = parser.parse_args()
    codes = consult()

    if args.all:
        for product in full_product_list(codes):
            print(product)
    
    elif args.all_open:
        for product in open_product_list(codes):
            print(product)

    elif args.header:
        for key in codes:
            print(key)
            
            for key in codes[key][0]:
                print('   %s' % key)
    
    elif args.selling:
        if args.loop:
            
            while True:
                show_selling(codes, args.games)
                sleep(27)
                print 'looping ',
                sleep(1)
                print '.',
                sleep(1)
                print '.',
                sleep(1)
                print '.'


if __name__ == '__main__':
    main()