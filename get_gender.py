from requests import get, RequestException
from bs4 import BeautifulSoup

def check_get(link):
    try:
        g = get(link)
    except RequestException as e:
        print(e)
        return None
    if g.ok and 'html' in g.headers['Content-Type']:
        return g

def get_gender(name):
    g = check_get('http://www.namespedia.com/details/{}'.format(name))
    if g is None:
        return None

    soup = BeautifulSoup(g.text, 'html.parser')

    s = str(soup.select('#content'))
    ind = s.find(r'% feminine')
    proc = s[ind-3: ind].split()
    proc = [elt for elt in proc if elt.isdigit()][0]

    gender = 'Masculine' if int(proc) < 50 else 'Feminine'

    return gender

if __name__ == '__main__':
    search_name = input('Input name: ')
    print('Gender: {0}'.format(get_gender(search_name)))
