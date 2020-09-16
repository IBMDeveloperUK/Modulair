import argparse
import json
import hashlib
import pathlib
import random
from tqdm import tqdm


from PIL import Image

import tensorflow.compat.v1 as tf
from object_detection.utils import dataset_util, label_map_util

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


def pick_modules_from_dir(data_dir='modules', count=1):
    data = list(pathlib.Path(data_dir).glob('./*.jpg'))
    result = []

    for _ in range(count):
        p = random.choice(data)
        result.append(Image.open(p.as_posix()))

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
                image = pathlib.Path(f'modules/{p["image"].split("/")[-1]}')
                if image.exists():
                    result[p["id"]]["image"] = Image.open(image.as_posix())
                    i += 1
    return result


def gen_tfrecord():
    page = random.randint(1, 5)
    jsonfile=f'modules/modules_page_{page}.json'
    modules = pick_modules_from_data(count=5, jsonfile=jsonfile)
    image, all_coords = join_modules([m["image"] for m in modules.values()])
    
    hash = hashlib.sha256()
    for i in [m.encode('utf-8') for m in modules]:
        hash.update(bytes(i))
    h = hash.hexdigest()[:8]
    filename = f'composites/modules_{h}.jpg'
    image.save(filename)

    xmins, xmaxs = [], []
    ymins, ymaxs = [], []
    classes_text, classes = [], []

    for i, d in enumerate(modules.values()):
        data = {k: v for k, v in d.items() if k != 'image'}
        x_min, x_max = all_coords[i]

        xmins.append(x_min)
        xmaxs.append(x_max)
        ymins.append(0)
        ymaxs.append(image.height)
        classes_text.append(data['name'].encode('utf-8'))
        classes.append(int(data['id']))
    
    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(image.height),
        'image/width': dataset_util.int64_feature(image.width),
        'image/filename': dataset_util.bytes_feature(filename.encode('utf-8')),
        'image/source_id': dataset_util.bytes_feature(filename.encode('utf-8')),
        'image/encoded': dataset_util.bytes_feature(open(filename, "rb").read()),
        'image/format': dataset_util.bytes_feature( b'jpg'),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))

    return tf_example


if __name__ == "__main__":

    filename = "train.tfrecords"
    writer = tf.python_io.TFRecordWriter(filename)
    
    for i in tqdm(range(1000)):
        tf_example = gen_tfrecord()
        writer.write(tf_example.SerializeToString())
    writer.close()
    print(f'Successfully created the TFRecord file with {i+1} records: {filename}')
