import argparse
import json
import hashlib
import pathlib
import random

from PIL import Image


def join_modules(modules):
    image = False
    all_coords = []
    height = max([i.height for i in modules])
    modules = [resize_image(i, height) for i in modules]
    width = sum([i.width for i in modules])
    return concat_images(height, width, modules)

def resize_image(image, height):
    if image.height == height:
        return image
    resample=Image.BICUBIC
    return image.resize(
        (int(image.width * height / image.height), height),
        resample=resample
    )

def concat_images(height, width, images):
    # Cribbed from https://note.nkmk.me/en/python-pillow-concat-images/
    dst = Image.new('RGB', (width, height))
    x = 0
    coords = []
    for image in images:
        dst.paste(image, (x, 0))
        coords.append((x, x + image.width))
        x = x + image.width
    return dst, coords


def pick_modules_from_dir(data_dir='data', count=1):
    data = list(pathlib.Path(data_dir).glob('./*.jpg'))
    result = []
    i = 0
    while i < count:
        p = random.choice(data)
        result.append(Image.open(p.as_posix()))
        i += 1
    return result


def pick_modules_from_data(jsonfile='data/modules_page_1.json', count=1):
    with open(jsonfile) as f:
        data = json.load(f)

    result = {}
    i = 0
    while i < count:
        p = random.choice(data)
        if p["id"] not in result:
            if '1u' not in p["name"].lower():
                result[p["id"]] = p
                image = pathlib.Path(f'data/{p["image"].split("/")[-1]}')
                if image.exists():
                    result[p["id"]]["image"] = Image.open(image.as_posix())
                    i += 1
    return result


if __name__ == "__main__":
    modules = pick_modules_from_data(count=5)
    image, all_coords = join_modules([m["image"] for m in modules.values()])


    hash = hashlib.sha256()
    for i in [m.encode('utf-8') for m in modules]:
        hash.update(bytes(i))
    h = hash.hexdigest()[:8]

    filename = f'modules_{h}.jpg'
    image.save(filename)
    to_save = []

    for i, d in enumerate(modules.values()):
        data = {k: v for k, v in d.items() if k != 'image'}
        data['x_min'], data['x_max'] = all_coords[i]
        to_save.append(data)
    with open(f'modules_{h}.json', 'w') as f:
        json.dump(to_save, f, indent=2, sort_keys=True)
