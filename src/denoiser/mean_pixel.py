from src.denoiser.base import Denoiser


@Denoiser.register_object()
class MeanPixel(Denoiser):

    def __init__(self, width, height):
        super(MeanPixel, self).__init__(width, height)

    def __get_mean(self, image, x, y, pos):
        r, g, b = [], [], []

        if (x + 1) < self.width:
            r.append(image[pos + 3])
            g.append(image[pos + 4])
            b.append(image[pos + 5])
        if (x - 1) > 0:
            r.append(image[pos - 3])
            g.append(image[pos - 2])
            b.append(image[pos - 1])
        if (y + 1) < self.height:
            r.append(image[pos + self.width * 3])
            g.append(image[pos + self.width * 3 + 1])
            b.append(image[pos + self.width * 3 + 2])
        if (y - 1) > 0:
            r.append(image[pos - self.width * 3])
            g.append(image[pos - self.width * 3 + 1])
            b.append(image[pos - self.width * 3 + 2])

        return sum(r)/len(r), sum(g)/len(g), sum(b)/len(b)

    def _denoise(self, image, connector):

        if connector:
            return connector.run_denoise(image, "mean")

        for y in range(self.height):
            for x in range((y + 1) % 2, self.width, 2):
                pos = y * self.width * 3 + x * 3
                r, g, b = self.__get_mean(image, x, y, pos)
                image[pos] = r
                image[pos + 1] = g
                image[pos + 2] = b

        return image
