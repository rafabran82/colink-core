import os
import traceback


def main():
    try:
        import matplotlib

        backend = os.environ.get("MPLBACKEND")
        if backend:
            matplotlib.use(backend, force=True)

        import matplotlib.pyplot as plt
        import numpy as np

        show = os.environ.get("SIM_SMOKE_SHOW", "0") == "1"
        hold = os.environ.get("SIM_SMOKE_HOLD", "0") == "1"
        out = os.environ.get("SIM_SMOKE_OUT")

        x = np.linspace(0, 2 * np.pi, 256)
        y = np.sin(x)

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(x, y)
        ax.set_title(f"Backend: {matplotlib.get_backend()}  |  show={show} hold={hold}")
        ax.set_xlabel("x")
        ax.set_ylabel("sin(x)")

        if out:
            fig.savefig(out, dpi=120)

        if show:
            # Avoid warnings under Agg (non-interactive)
            bname = str(matplotlib.get_backend()).lower()
            if "agg" not in bname:
                plt.show(block=hold)

        print("OK:", matplotlib.get_backend())
        return 0
    except Exception as e:
        print("SMOKE ERROR:", e)
        traceback.print_exc()
        return 0 if os.environ.get("SIM_SMOKE_SOFTFAIL", "0") == "1" else 1


if __name__ == "__main__":
    raise SystemExit(main())

