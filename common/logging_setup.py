import logging

def setup(verbose: bool=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s"
    )
    return logging.getLogger("is2")
