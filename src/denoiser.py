import cv2

import numpy as np


class Denoiser(object):

    def __init__(self, width, height):
        self.width = width,
        self.height = height
        self.sequence = []

    def denoise(self, image):
        image = image.reshape(300, 300, 3)
        image = image.astype(np.uint8, copy=False)
        # self.sequence.append(image)
        # if len(self.sequence) > 5:
        #    self.sequence.pop(0)

        # if len(self.sequence) != 5:
        #    return image

        return cv2.fastNlMeansDenoisingColored(
                image, None, 10, 10, 21, 21)
