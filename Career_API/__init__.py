import os, sys
import aiorwlock
from datetime import timedelta
from quart import Quart

from Career_API import utils
from Career_API.utils import *
from Career_API.controller import backend


async def init_server():
    if utils.LOCK_OCTREE is None:
        utils.LOCK_OCTREE = aiorwlock.RWLock()


def create_app():
    app = Quart(__name__, template_folder='demo', static_folder='demo', static_url_path='')
    app.config['JSON_AS_ASCII'] = False
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'csv', 'xlsx', 'xls', 'doc', 'docx', 'png', 'jpg', 'pdf'}
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'upload')
    app.config['OUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'out')
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
    app.jinja_env.variable_start_string = '<<'
    app.jinja_env.variable_end_string = '>>'

    app.register_blueprint(backend)

    app.before_serving(init_server)
    app.run(host='0.0.0.0', port=2334)

