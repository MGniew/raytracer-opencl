import argparse
from src.engine import Engine


def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("--w", type=int, default=300)
    parser.add_argument("--h", type=int, default=300)
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("--noise", type=int, default=1)
    parser.add_argument("--scene", type=str, default="scenes/scene.json")
    parser.add_argument("--obj", type=str, default=None)

    return parser.parse_args()


def main():

    args = get_args()
    engine = Engine(
        "kernels/raytracer.cl",
        args.scene,
        args.w,
        args.h,
        args.noise,
        args.obj)
    engine.run()


if __name__ == "__main__":
    main()
