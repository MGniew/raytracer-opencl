from PIL import Image
from PIL import ImageShow
import os
from src.denoiser.mean_pixel import MeanPixel
from src.denoiser.median_pixel import MedianPixel
from src.denoiser.cnn import CnnAutoencoder
import numpy as np
from PIL import ImageFilter


class FehViewer(ImageShow.UnixViewer):
    def show_file(self, filename, **options):
        os.system('feh %s' % filename)
        return 1

ImageShow.register(FehViewer, order=-1)


def load_image(filename):

    img = Image.open(filename)
    img.load()
    data = np.asarray(img, dtype=np.uint8)
    return data.flatten()


def show_image_numpy(im):
    im = Image.fromarray(im.reshape(480, 720, 3))
    im.save("1.png")
    im.show()


denoiser = MeanPixel(720, 480)
original_image = load_image("./animations/animation_single/0.png")
noise_image = load_image("./animations/animation_single_noise/0.png")
print(denoiser.get_distance(original_image, original_image))
print(denoiser.get_distance(original_image, noise_image))

# ni = np.copy(noise_image)
# ni = denoiser.denoise(ni, None)
# print(denoiser.get_distance(ni, original_image))
# show_image_numpy(ni)
# 
# denoiser = MedianPixel(720, 480)
# ni = np.copy(noise_image)
# ni = denoiser.denoise(ni, None)
# print(denoiser.get_distance(ni, original_image))
# show_image_numpy(ni)

denoiser = CnnAutoencoder(720, 480)
ni = np.copy(noise_image)
print(1)
ni = denoiser.denoise(ni, None)
print(2)
print(denoiser.get_distance(ni, original_image))
show_image_numpy(ni)






