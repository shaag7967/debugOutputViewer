import sys
from application import Application

# check minimum python version
MIN_PYTHON = (3, 11)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required." % MIN_PYTHON)

# start application
app = Application(sys.argv)
sys.exit(app.exec())
