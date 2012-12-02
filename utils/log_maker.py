import logging

def make_logger(name = "BSE"):
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler(name + '.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)

    return logger