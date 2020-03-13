import logging


__all__ = ["logger"]

logger = logging.getLogger("main")
formatter = logging.Formatter("%(levelname)s - IMPORTER - %(message)s")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
