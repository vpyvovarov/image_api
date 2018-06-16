import logging
import os
import sqlite3
import uuid

from io import BytesIO
from flask import Flask, send_file
from flask_restful import Resource, Api, reqparse
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# folder to which images will be saved
STORAGE_FOLDER = './storage'
DB_NAME = 'image_api_db'


def get_logger():
    """
    Use out own logger because we have classes that also require logger
    """
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


APP = Flask(__name__)
API = Api(APP)


# create storage directory if it doesn't exists
if not os.path.exists(STORAGE_FOLDER):
    os.makedirs(STORAGE_FOLDER)


# disable flask logging and use custom logger
logging.getLogger('werkzeug').setLevel(logging.ERROR)


LOG = get_logger()
LOG.info("Image Api started")


class DB:
    """ Class for all DB related stuff"""
    def __init__(self):
        # XXX: under high load this is inefficient. We have to make this
        # class singleton with pool of DB connections
        # XXX: creating tables and DAO models omitted for sake of simplicity
        self.db = sqlite3.connect(DB_NAME)

    def add_image_record(self, _id, path, filename):
        cursor = self.db.cursor()
        cursor.execute(
            'INSERT INTO images(id, storage_path, filename) VALUES(?,?,?)',
            (_id, path, filename))

        self.db.commit()
        LOG.info("Add image info to DB")

    def get_image_info(self, _id):
        cursor = self.db.cursor()
        cursor.execute(
            'SELECT storage_path, filename from images where id=?', (_id, ))
        data = cursor.fetchone()
        LOG.info("Get image info to DB")
        return data


class ImageObject:
    """ Class that represrnt image and all image related operation"""
    def __init__(self, file_path):
        self.img = Image.open(file_path)

    def zoom(self, zoom):
        zoom_factor = 2 ** zoom
        zoomed_size = [int(size / zoom_factor) for size in self.img.size]
        self.img = self.img.resize(zoomed_size, Image.ANTIALIAS)
        LOG.info("Zoom image done")

    def crop(self, left, top, right, bottom):
        x_max, y_max = self.img.size
        left = min([left, x_max])
        right = min([right, x_max])
        top = min([top, y_max])
        bottom = min([bottom, y_max])
        self.img = self.img.crop((left, top, right, bottom))
        LOG.info("Crop image done")

    def save_to_temp_file(self, filename):
        _file = BytesIO()
        _file.name = filename
        self.img.save(_file)
        _file.seek(0)
        return _file


class ImageUploadAPI(Resource):
    """Image upload handler"""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('file', type=FileStorage, location='files')
        self.db = DB()
        super().__init__()

    def post(self):
        """On  file upload:
            1. Assign uuid to file, because files could have the same name.
            2. Save file to storage folder.
            3. Create record in DB to tight uuid, path on
               the storage and real file name
            4. Return uuid to user
        """
        LOG.info("Image upload started")
        args = self.parser.parse_args()

        upload_file = args['file']
        upload_file.filename = secure_filename(upload_file.filename)

        _id = str(uuid.uuid4())
        path_on_storage = os.path.join(STORAGE_FOLDER, _id)
        upload_file.save(path_on_storage)
        self.db.add_image_record(_id, path_on_storage, upload_file.filename)
        LOG.info("Image upload done")
        return {'id': _id}


class ImageDownloadAPI(Resource):
    """Image download handler"""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('zoom', type=float)
        self.parser.add_argument('left', type=int)
        self.parser.add_argument('right', type=int)
        self.parser.add_argument('top', type=int)
        self.parser.add_argument('bottom', type=int)
        self.db = DB()
        super().__init__()

    def get(self, _id):
        """
        Zoom, crop and return image

        :param _id: str. uuid of image returned at upload
        :return:
        """
        LOG.info("Image preparation stated")
        args = self.parser.parse_args()
        record = self.db.get_image_info(_id)

        if not record:
            LOG.error("Can't find file")
            return {'error': 'id not found'}, 404
        path_on_storage, filename = record

        img = ImageObject(path_on_storage)
        img.zoom(args['zoom'])
        img.crop(args['left'], args['top'], args['right'], args['bottom'])
        _file = img.save_to_temp_file(filename)
        LOG.info("Image ready for download")
        return send_file(_file, attachment_filename=filename)


API.add_resource(ImageUploadAPI, '/upload')
API.add_resource(ImageDownloadAPI, '/download/<string:_id>')


if __name__ == '__main__':
    APP.run()
