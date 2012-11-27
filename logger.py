import logging

def make_logger(name):
    logger = logging.getLogger('trader_AA')
    hdlr = logging.FileHandler('trader_AA.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)