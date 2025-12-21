""" module to handle minio operations like upload and download
"""
import logging
import time
from minio import Minio
from pylclient.secrets.secret import Secret
import yaml

logger = logging.getLogger(__name__)
MINIO_VAULT = "tests/connectortests/minio_users"


class MinIOWrapper():
    """
    class to upload and download files to MinIO Server.
    """

    def __init__(self, variables):
        minio_config_dict = {}
        if variables:
            minio_config_dict = variables['minio']
        else:
            with open("config/environment/dynamic.local.yml", "r") as stream:
                envi_config = yaml.safe_load(stream)
                minio_config_dict = envi_config['minio']


        minio_server = "{}:{}".format(minio_config_dict['ip'],
                                      minio_config_dict['port'])
        secret = Secret(MINIO_VAULT)
        user_credentials = secret.get(minio_config_dict["account_name"])
        minio_access_key = user_credentials['access_key']
        minio_secret_key = user_credentials['secret_key']
        self.client = Minio(minio_server,
                            access_key=minio_access_key,
                            secret_key=minio_secret_key, secure=False)

    def download_file(self, bucket_name, file_name, file_path):
        """
        download file from minio server
        """
        logger.info('downloading file: %s from bucket %s to the path %s',
                    file_name, bucket_name, file_path)

        try:
            self.client.fget_object(bucket_name, file_name, file_path)
            time.sleep(3)
        except Exception as no_such_key_exp:
            logger.error("File %s is not available in the bucket %s",
                         file_name, bucket_name)
            raise no_such_key_exp

    def list_objects(self, bucket_name, filter):
        """
        download file from minio server
        """
        logger.info('getting list of files: %s from bucket %s',
                    filter, bucket_name)

        try:
            return self.client.list_objects(bucket_name, filter, recursive=True)
        except NoSuchKey as no_such_key_exp:
            logger.error("Error retriving file list from bucket %s", bucket_name)
            raise no_such_key_exp


    def download_folder(self, bucket_name, folder_path):
            """
            download file from minio server
            """
            logger.info('downloading file: %s from bucket %s to the path %s',
                        file_name, bucket_name, file_path)

            try:
                self.client.fget_object(bucket_name, file_name, file_path)
                time.sleep(3)
            except NoSuchKey as no_such_key_exp:
                logger.error("File %s is not available in the bucket %s",
                             file_name, bucket_name)
                raise no_such_key_exp

    def upload_file(self, bucket_name, file_name, file_path):
        """
        upload file to minio server
        """
        logger.info('uploading file: %s from bucket %s to the path %s',
                    file_name, bucket_name, file_path)
        try:
            self.client.fput_object(bucket_name, file_name, file_path)
            time.sleep(3)
        except Exception:
            logger.error("File %s is not available in the bucket %s",
                         file_name, bucket_name)
