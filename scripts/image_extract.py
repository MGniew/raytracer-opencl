from PIL import Image
from PIL import ImageShow
import random
import os
from src.denoiser.mean_pixel import MeanPixel
from src.denoiser.median_pixel import MedianPixel
import numpy as np
from PIL import ImageFilter


def load_image(filename):
    img = Image.open(filename)
    img.load()
    data = np.asarray(img, dtype=np.uint8)
    return data


def file_generator(root):
    for root, dirs, files in os.walk(root):
        for name in files:
            yield os.path.join(root, name)


def get_random_window(image):
    h, w, d = image.shape
    rh = random.randint(0, h - 150)
    rw = random.randint(0, w - 150)

    return image[rh:rh+150, rw:rw+150, :]


def get_image_with_noise(image):

    result = np.copy(image)
    for row in range(image.shape[0]):
        mod_col = 0
        if row % 2 == 0:
            mod_col = 1
        for col in range(image.shape[1]):
            if col % 2 == mod_col:
                result[row, col, :] = 0

    return result


for i, filename in enumerate(file_generator("animation_single")):
    image = load_image(filename)
    h, w, d = image.shape
    if h < 150 or w < 150:
        continue

    random_window = get_random_window(image)
    random_window_noised = get_image_with_noise(random_window)
    im = Image.fromarray(random_window)
    im2 = Image.fromarray(random_window_noised)
    im.save("out/" + str(i) + ".png")
    im2.save("out_noise/" + str(i) + ".png")
