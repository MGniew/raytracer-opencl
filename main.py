import argparse

from src.engine import Engine


def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("--w", type=int, default=300)
    parser.add_argument("--h", type=int, default=300)
    parser.add_argument("--no-gui", action="store_true")

    return parser.parse_args()


def main():

    args = get_args()
    engine = Engine(
        # "kernels/mandelbulb.cl",
        "kernels/raytracer.cl",
        "scenes/scene.json",
        args.w,
        args.h)
    engine.run()


if __name__ == "__main__":
    main()
