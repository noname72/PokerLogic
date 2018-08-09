from requests import get, RequestException
from bs4 import BeautifulSoup

def check_get(link):
    try:
        g = get(link, timeout = 2)
    except RequestException as e:
        print(e)
        return None

    if g.ok and 'html' in g.headers['Content-Type'] and g.status_code == 200:
        return g

def get_gender(name):
    g = check_get('http://www.namespedia.com/details/{}'.format(name))
    if g is None:
        return None

    soup = BeautifulSoup(g.text, 'html.parser')
    content = str(soup.select('#content'))
    ind = content.find(r'% feminine')
    if ind == -1:
        return None

    proc = content[ind-3: ind].split()
    proc = [elt for elt in proc if elt.isdigit()][0]

    gender = 'Male' if int(proc) < 50 else 'Female'
    return gender

if __name__ == '__main__':
    search_name = input('Input name: ')
    print('Gender: {0}'.format(get_gender(search_name)))
