from app import config
if config.DEBUG:
    print('starting ...')
from app.main import main_loop

main_loop()
