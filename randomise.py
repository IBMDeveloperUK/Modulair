import argparse
import json
import hashlib
import pathlib
import random

from PIL import Image


def join_modules(modules):
    image = False
    all_coords = []
    while len(modules):
        if image:
            image, coords = get_concat_h_resize(image, modules.pop())
        else:
            image, coords = get_concat_h_resize(modules.pop(), modules.pop())
        all_coords.append(coords)
    return image, all_coords


def get_concat_h_resize(im1, im2, resample=Image.BICUBIC, resize_big_image=True):
    # Cribbed from https://note.nkmk.me/en/python-pillow-concat-images/
    if im1.height == im2.height:
        _im1 = im1
        _im2 = im2
    elif (((im1.height > im2.height) and resize_big_image) or
          ((im1.height < im2.height) and not resize_big_image)):
        _im1 = im1.resize(
            (int(im1.width * im2.height / im1.height), im2.height), resample=resample)
        _im2 = im2
    else:
        _im1 = im1
        _im2 = im2.resize(
            (int(im2.width * im1.height / im2.height), im1.height), resample=resample)
    dst = Image.new('RGB', (_im1.width + _im2.width, _im1.height))
    dst.paste(_im1, (0, 0))
    dst.paste(_im2, (_im1.width, 0))
    return dst, (dst.width, dst.height, _im1.width, _im2.width)


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
    print(all_coords)
    hash = hashlib.sha256()
    for i in [m.encode('utf-8') for m in modules]:
        hash.update(bytes(i))
    h = hash.hexdigest()[:8]
    image.save(f'modules_{h}.jpg')
    to_save = []
    for d in modules.values():
        to_save.append({k: v for k, v in d.items() if k != 'image'})
    with open(f'modules_{h}.json', 'w') as f:
        json.dump(to_save, f)
