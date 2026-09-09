from multiprocessing import ProcessError

import shutdown_process_1 as shutdown
import startup_process_2 as startup

def main() -> None:
    try:
        startup.main()
        shutdown.main()

    except ProcessError as e:
        print(e)