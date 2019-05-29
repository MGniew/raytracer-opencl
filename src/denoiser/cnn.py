import numpy as np
from keras.models import load_model
from src.denoiser.base import Denoiser


@Denoiser.register_object()
class CnnAutoencoder(Denoiser):

    def __init__(self, width, height):
        super(CnnAutoencoder, self).__init__(width, height)
        self.model = None

    def load_model(self, filename):
        self.model = load_model(filename)

    def split_array(self, image, block_size=120):

        if self.height < block_size:
            image = np.pad(image, (
                (0, block_size - self.height)),
                "constant")
        if self.width < block_size:
            image = np.pad(image, (
                (0, block_size - self.width)),
                "constant")
        if self.height == self.width == block_size:
            return [image]

        result = []
        bot_h = 0
        up_h = block_size
        bot_w = 0
        up_w = block_size

        while bot_w < self.width:
            row = []
            while bot_h < self.height:
                row.append(image[bot_h:up_h, bot_w:up_w])
                bot_h += block_size
                up_h += block_size
            result.append(row)
            bot_w += block_size
            up_w += block_size

        return result

    def merge_array(self, chunks, block_size=120):

        rows = [np.concatenate(row, axis=1) for row in chunks]
        result = np.concatenate(rows, axis=0)
        return result

    def predict(self, chunk):
        return self.model.predict(chunk)

    def _denoise(self, image, connector):

        image = image/255
        chunks = self.split_array(image)
        chunks = map(self.predict, chunks)
        image = self.merge_array(chunks)
        image = image * 255

        return image
