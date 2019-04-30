from sklearn.metrics import mean_squared_error


class Denoiser(object):

    subclasses = {}

    @classmethod
    def register_object(cls):

        def decorator(subclass):
            cls.subclasses[subclass.__name__] = subclass
            return subclass

        return decorator

    @classmethod
    def create(cls, name, *args):

        if name not in cls.subclasses:
            raise ValueError("Bad object name: {}".format(name))
        return cls.subclasses[name](*args)

    @staticmethod
    def get_distance(image1, image2):
        return mean_squared_error(image1, image2)

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.sequence = []

    def denoise(self, image, connector):
        return self._denoise(image, connector)

        # image = image.reshape(300, 300, 3)
        # image = image.astype(np.uint8, copy=False)
        # self.sequence.append(image)
        # if len(self.sequence) > 5:
        #    self.sequence.pop(0)

        # if len(self.sequence) != 5:
        #    return image

        # return cv2.fastNlMeansDenoisingColored(
        #         image, None, 10, 10, 21, 21)
