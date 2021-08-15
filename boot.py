import os

# check if there is an update
try:
    os.stat('/next')
    os.rename('/app/config.py', '/next/config.py')
    os.rename('/app', '/old')
    os.rename('/next', '/app')
    for old_file in os.listdir('/old'):
        os.remove('/old/%s' % old_file)
    os.remove('/old')
except OSError:
    pass

from app.main import main_loop

main_loop()
