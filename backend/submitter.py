from multiprocessing import Process


def main():
    pass

def run_submitter() -> Process:
    p = Process(target=main)
    p.start()
    return p