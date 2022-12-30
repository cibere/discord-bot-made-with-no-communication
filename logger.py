import datetime
import logging
import pathlib
import sys
from logging.handlers import TimedRotatingFileHandler


def init():
    logginglevel = logging.INFO
    dircheck = pathlib.Path.exists(pathlib.Path.cwd().joinpath('logs'))
    if dircheck != True:
        print('Making Log Directory...')
        pathlib.Path.mkdir(pathlib.Path.cwd().joinpath('logs'))

    logging.basicConfig(
        level=logginglevel,
        format='%(asctime)s [%(levelname)s]  %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        handlers=[
            logging.StreamHandler(sys.stdout),
            TimedRotatingFileHandler(
                pathlib.Path.as_posix(pathlib.Path.cwd().joinpath('logs')) + '/log',
                'midnight',
                atTime=datetime.datetime.min.time(),
                backupCount=4,
                encoding='utf-8',
                utc=True,
            ),
        ],
    )
