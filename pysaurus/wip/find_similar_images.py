#!/usr/bin/env python
"""
Demo of hashing
"""
from __future__ import (absolute_import, division, print_function)

import mimetypes
import os
import sys
import traceback

import imagehash
from PIL import Image
from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.utils.classes import StringPrinter


def similar_group_to_html_file(group_id, images, html_dir):
    size = len(images)
    html = StringPrinter()
    html.write('<html>')
    html.write('<header>')
    html.write('<meta charset="utf-8"/>')
    html.write('<title>Thumbnails similarities for group %s</title>' % group_id)
    html.write('<link rel="stylesheet" href="similarities.css"/>')
    html.write('</header>')
    html.write('<body>')
    html.write('<h1>%d files</h1>' % size)
    html.write('<table>')
    html.write('<thead>')
    html.write('<tr><th class="group-id">Group ID</th><th class="thumbnails">Thumbnails</th></tr>')
    html.write('<tbody>')
    html.write('<tr>')
    html.write('<td class="group-id">%s</td>' % group_id)
    html.write('<td class="thumbnails">')
    for thumb_path in images:
        html.write('<div class="thumbnail">')
        html.write('<div class="image">')
        html.write('<img src="file://%s"/>' % thumb_path)
        html.write('</div>')
        html.write('<div><code>%s</code></div>' % thumb_path)
        html.write('</div>')
    html.write('</td>')
    html.write('</tr>')
    html.write('</tbody>')
    html.write('</thead>')
    html.write('</table>')
    html.write('</body>')
    html.write('</html>')

    output_file_name = AbsolutePath.join(html_dir, 'sim.%s.html' % (group_id))
    os.makedirs(html_dir, exist_ok=True)
    with open(output_file_name.path, 'w') as file:
        file.write(str(html))


def is_image(filename):
    file_type, _ = mimetypes.guess_type(filename)
    return file_type is not None and file_type.startswith('image/')


def find_similar_images(user_paths, hash_func=imagehash.average_hash):
    images = {}
    nb_images = 0
    print('Hashing images')
    for user_path in user_paths:
        for path in os.listdir(user_path):
            if is_image(path):
                img = os.path.join(user_path, path)
                try:
                    images.setdefault(hash_func(Image.open(img)), []).append(img)
                    nb_images += 1
                    if nb_images % 100 == 0:
                        print('Hashed', nb_images, 'images')
                except Exception as e:
                    print('Error with image', img)
                    traceback.print_tb(e.__traceback__)
                    print(e)
    print('Finished hashing', nb_images, 'images')
    print('Found', len(images), 'hashes')

    # image_hashes = list(images)
    # nb_hashes = len(image_hashes)
    # sizes = {image_hash.hash.size for image_hash in image_hashes}
    # hash_size = 0
    # diff_limit = 0.9
    # if len(sizes) == 1:
    #     hash_size = next(iter(sizes))
    #     print('Hash size:', hash_size)
    # else:
    #     print('Cannot compare images with different hash sizes')
    #     exit(-1)
    # print('Comparing', nb_hashes, 'hashes')
    # classes = list(range(len(image_hashes)))
    # max_c = int(nb_hashes * (nb_hashes - 1) / 2)
    # for i in range(len(image_hashes)):
    #     hash_i = image_hashes[i]
    #     for j in range(i + 1, len(image_hashes)):
    #         normalized_diff = (hash_i - image_hashes[j]) / hash_size
    #         if normalized_diff >= diff_limit:
    #             classes[j] = classes[i]
    #     print('Comparing hash', i + 1, '/', nb_hashes)
    # groups = {}
    # for hash_index, hash_class in enumerate(classes):
    #     groups.setdefault(hash_class, []).extend(images[image_hashes[hash_index]])
    # valid_groups = [group for group in groups.values() if len(group) > 1]
    # if valid_groups:
    #     print('Found', len(valid_groups), 'groups')
    #     min_size = min(len(group) for group in valid_groups)
    #     max_size = max(len(group) for group in valid_groups)
    #     print('Min size', min_size)
    #     print('Max size', max_size)

    print()
    print()
    print('================')
    print('IDENTICAL IMAGES')
    print('================')
    for image_hash, identical_images in images.items():
        if len(identical_images) > 1:
            print(image_hash)
            for img in identical_images:
                print('\t%s' % img)
            similar_group_to_html_file(image_hash, identical_images, '.similar')


def usage():
    sys.stderr.write("""SYNOPSIS: %s [ahash|phash|dhash|...] [<directory>]

Identifies similar images in the directory.

Method: 
ahash:      Average hash
phash:      Perceptual hash
dhash:      Difference hash
whash-haar: Haar wavelet hash
whash-db4:  Daubechies wavelet hash

(C) Johannes Buchner, 2013-2017
""" % sys.argv[0])


def main():
    hash_method = sys.argv[1] if len(sys.argv) > 1 else ''
    if hash_method == 'ahash':
        hash_func = imagehash.average_hash
    elif hash_method == 'phash':
        hash_func = imagehash.phash
    elif hash_method == 'dhash':
        hash_func = imagehash.dhash
    elif hash_method == 'whash-haar':
        hash_func = imagehash.whash
    elif hash_method == 'whash-db4':
        hash_func = lambda img: imagehash.whash(img, mode='db4')
    else:
        return usage()
    userpaths = sys.argv[2:] if len(sys.argv) > 2 else "."
    find_similar_images(user_paths=userpaths, hash_func=hash_func)


if __name__ == '__main__':
    main()
