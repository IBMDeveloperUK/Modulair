import json
import pathlib
import re
import time

import requests

from bs4 import BeautifulSoup


def get_search(page=0):
    url = 'https://www.modulargrid.net/e/modules/find'
    if page:
        url = f"{url}/page:{page}"
    response = requests.get(
        url,
        params={
            'SearchTemethod': 'max',
            'SearchIsmodeled': 0,
            'SearchShowothers': 0,
            'order': 'newest',
            'direction': 'asc',
        },
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.modulargrid.net/e/modules/browser?SearchName=&SearchVendor=&SearchFunction=&SearchSecondaryfunction=&SearchHeight=&SearchTe=&SearchTemethod=max&SearchBuildtype=&SearchLifecycle=&SearchSet=&SearchMarketplace=&SearchIsmodeled=0&SearchShowothers=0&order=newest&direction=asc'
        }
    )
    response.raise_for_status()
    return response.text


def parse_results(results):
    img_root = 'https://www.modulargrid.net/img/modcache/'
    soup = BeautifulSoup(results, features="html.parser")
    modules = []
    for module in soup.find_all('div', class_="box-module"):
        t_module = {
            'id': module['data-module-id'],
            'image': f'{img_root}{module["data-module-id"]}.f.jpg',
            'info': []
        }
        for label in module.find_all(class_='label'):
            if 'label-info' in label['class']:
                t_module['info'].append(label.text)
            else:
                t_module['size'] = label.text
        for name in module.find_all(class_='module-name'):
            if name.name == 'h3':
                t_module['name'] = name.text
            elif name.name == 'h4':
                t_module['manufacturer'] = name.text
        t_module['description'] = module.find(class_='txt-ellipsis').text
        modules.append(t_module)
    # next = soup.find('a', id='lnk-next-results')
    # m = re.search('page:(\d)\?', str(next.href))
    return modules #, m.group(1)

def save_images(data):
    for module in data:
        print(module["id"], module["image"])
        r = requests.get(module["image"], stream=True)
        r.raise_for_status()
        with open(module["image"].split('/')[-1], 'wb') as f:
            for chunk in r:
                f.write(chunk)


if __name__ == "__main__":
    next = 1
    ok = True

    while ok:
        print(f'in a loop, page {next}')
        try:
            results = get_search(next)
            data = parse_results(results)
            with open(f'modules_page_{next}.json', 'w') as f:
                json.dump(data, f)
            save_images(data)
            time.sleep(2)
            next += 1
            if next > 5:
                ok = False
        except Exception as e:
            print(e)
            ok = False
