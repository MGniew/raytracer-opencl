import numpy as np
from keras.models import load_model
from src.denoiser.base import Denoiser


@Denoiser.register_object()
class CnnAutoencoder(Denoiser):

    def __init__(self, width, height):
        super(CnnAutoencoder, self).__init__(width, height)
        self.model = None
        self.load_model("cnn_models/model4_short.hdf5")

    def load_model(self, filename):
        self.model = load_model(filename)

    def split_array(self, image, block_size=120):
        rows = np.split(image, self.height/block_size, axis=0)
        result = [np.split(r, self.width/block_size, axis=1) for r in rows]
        result = [item for sublist in result for item in sublist]
        return np.stack(result)

    def split_array_old(self, image, block_size=120):

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

        while bot_h < self.height:
            row = []
            while bot_w < self.width:
                row.append(image[bot_h:up_h, bot_w:up_w,:])
                bot_w += block_size
                up_w += block_size
            result.append(row)
            bot_h += block_size
            up_h += block_size
            bot_w = 0
            up_w = block_size

        return result

    def merge_array(self, chunks, block_size=120):
        result = [chunks[i, ...] for i in range(chunks.shape[0])]
        bpr = self.width//block_size
        result = [result[i:i+bpr] for i in range(0, len(result), bpr)]
        result = [np.stack(r, axis=1) for r in result]
        result = np.stack(result, axis=0)

        return result

    # def merge_array(self, chunks, block_size=120):

    #     rows = [np.concatenate(row, axis=1) for row in chunks]
    #     result = np.concatenate(rows, axis=0)
    #     return result

    def predict(self, chunk):
        # chunk = np.expand_dims(chunk, axis=0)
        # return np.squeeze(self.model.predict(chunk))
        return self.model.predict(chunk)

    def _denoise(self, image, connector):

        image = image/255
        image = np.reshape(image, (self.height, self.width, 3))
        chunks = self.split_array(image)
        predicted = self.predict(chunks)
        # predicted = []
        # for row in chunks:
        #     row_pred = []
        #     for chunk in row:
        #         pred = self.predict(chunk)
        #         row_pred.append(pred)
        #     predicted.append(row_pred)
        image = self.merge_array(predicted)
        image = np.round(image * 255)
        return image.flatten().astype("uint8")
