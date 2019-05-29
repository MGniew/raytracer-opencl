from src.denoiser.base import Denoiser


# https://www.comm.utoronto.ca/~kostas/Publications2008/pub/proceed/38.pdf
@Denoiser.register_object()
class MedianPixel(Denoiser):

    def __init__(self, width, height):
        super(MedianPixel, self).__init__(width, height)

    def __get_mean(self, image, x, y, pos):
        pixels = []

        if (x + 1) < self.width:
            pixels.append(
                    (image[pos + 3],
                     image[pos + 4],
                     image[pos + 5]))
        if (x - 1) > 0:
            pixels.append(
                    (image[pos - 3],
                     image[pos - 2],
                     image[pos - 1]))
        if (y + 1) < self.height:
            pixels.append(
                    (image[pos + self.width * 3],
                     image[pos + self.width * 3 + 1],
                     image[pos + self.width * 3 + 2]))
        if (y - 1) > 0:
            pixels.append(
                    (image[pos - self.width * 3],
                     image[pos - self.width * 3 + 1],
                     image[pos - self.width * 3 + 2]))

        median_pixel_index = 0
        dist = 0
        for k in range(len(pixels)):
            if k != 0:
                dist += self.__get_pixel_distance(
                        pixels[0], pixels[k])

        for i in range(1, len(pixels)):
            diff_sum = 0
            for k in range(len(pixels)):
                if i != k:
                    diff_sum += self.__get_pixel_distance(
                            pixels[i], pixels[k])
            if dist > diff_sum:
                diff_sum = dist
                median_pixel_index = i

        return pixels[median_pixel_index]

    def __get_pixel_distance(self, pixel_a, pixel_b, norm=1):

        if len(pixel_a) != len(pixel_b):
            raise Exception("Wrong pixel size")

        diff = [v - pixel_b[i] for i, v in enumerate(pixel_a)]
        diff = sum([v**norm for v in diff])
        diff = diff**(1/3)
        return diff

    def _denoise(self, image, connector):

        if connector:
            return connector.run_denoise(image)

        for y in range(self.height):
            for x in range((y + 1) % 2, self.width, 2):
                pos = y * self.width * 3 + x * 3
                r, g, b = self.__get_mean(image, x, y, pos)
                image[pos] = r
                image[pos + 1] = g
                image[pos + 2] = b

        return image
