"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import os
import io
import csv
import ssl
import uuid
import pickle
import logging
try:
    import ujson as json
except:
    import json

from dateutil import parser
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from .models import FileUpload

logger = logging.getLogger(__name__)
csv.field_size_limit(131072 * 10)


def is_binary(f):
    return isinstance(f, (io.RawIOBase, io.BufferedIOBase))


def csv_generate_header(file):
    """ Generate column names for headless csv file """
    file.seek(0)
    names = []
    line = file.readline()

    num_columns = len(line.split(b',' if isinstance(line, bytes) else ','))
    for i in range(num_columns):
        names.append('column' + str(i+1))
    file.seek(0)
    return names


def check_max_task_number(tasks):
    # max tasks
    if len(tasks) > settings.TASKS_MAX_NUMBER:
        raise ValidationError(f'Maximum task number is {settings.TASKS_MAX_NUMBER}, '
                              f'current task number is {len(tasks)}')


def check_file_sizes_and_number(files):
    total = sum([file.size for _, file in files.items()])

    if total >= settings.TASKS_MAX_FILE_SIZE:
        raise ValidationError(f'Maximum total size of all files is {settings.TASKS_MAX_FILE_SIZE} bytes, '
                              f'current size is {total} bytes')


def create_file_upload(request, project, file):
    instance = FileUpload(user=request.user, project=project, file=file)
    instance.save()
    return instance


def str_to_json(data):
    try:
        json_acceptable_string = data.replace("'", "\"")
        return json.loads(json_acceptable_string)
    except ValueError:
        return None

def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False

def tasks_from_url(file_upload_ids, project, request, url):
    """ Download file using URL and read tasks from it
    """
    print("dadadadadadadadadadadaaaaaaaaaaaaaaaaaaaaaaaaa")
    print(file_upload_ids)
    print(project)
    print(request)
    if uri_validator(url) == True:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        print("dadadadasdjlshakjdhkajshdjkhasdjkhasd")
        print(request)
        print(project)
        print(file_upload_ids)
        try:
            filename = url.rsplit('/', 1)[-1]
            with urlopen(url, context=ctx) as file:
                # check size
                meta = file.info()
                file.size = int(meta.get("Content-Length"))
                file.urlopen = True
                check_file_sizes_and_number({url: file})
                file_content = file.read()
                if isinstance(file_content, str):
                    file_content = file_content.encode()
                file_upload = create_file_upload(request, project, SimpleUploadedFile(filename, file_content))
                file_upload_ids.append(file_upload.id)
                print(file_upload_ids)
                tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)
                print(tasks)
                print(found_formats)
                print(data_keys)

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(str(e))
    else:
        url_array = url.split("/", 1)

        url = url_array[1]
        print(url)
        url_token = url_array[0]
        req = Request(url)
        req.add_header('Authorization', 'Bearer '+ url_token)
        # process URL with tasks
        ctx = ssl.create_default_context()
        print(req)
        # print(url_token)
        
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            filename = url.rsplit('/', 1)[-1] + '.jpg'
            print("ten tente tententnetnet")
            print(filename)
            with urlopen(req, context=ctx) as file:
                # check size
                meta = file.info()
                print(file.info())
                print(meta)
                file.size = int(400)
                file.urlopen = True
                check_file_sizes_and_number({url: file})
                file_content = file.read()
                if isinstance(file_content, str):
                    file_content = file_content.encode()
                file_upload = create_file_upload(request, project, SimpleUploadedFile(filename, file_content))
                file_upload_ids.append(file_upload.id)
                tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)


        
        # file_content_raw = urlopen(req,context=ctx)
        # # meta = file_content_raw.info()
        # file_content_raw.size = int(400)
        # file_content_raw.urlopen = True
        # check_file_sizes_and_number({url: file_content_raw})
        # file_content = file_content_raw.read()
        # if isinstance(file_content, str):
        #     file_content = file_content.encode()
        # file_upload = create_file_upload(request, project, SimpleUploadedFile(filename, file_content))
        # file_upload_ids.append(file_upload.id)
        # tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(str(e))
    return data_keys, found_formats, tasks, file_upload_ids

    
def load_tasks(request, project):
    """ Load tasks from different types of request.data / request.files
    """
    file_upload_ids, found_formats, data_keys = [], [], set()
    could_be_tasks_lists = False

    # take tasks from request FILES
    if len(request.FILES):
        check_file_sizes_and_number(request.FILES)
        for filename, file in request.FILES.items():
            file_upload = create_file_upload(request, project, file)
            if file_upload.format_could_be_tasks_list:
                could_be_tasks_lists = True
            file_upload_ids.append(file_upload.id)
        tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)

    # take tasks from url address
    elif 'application/x-www-form-urlencoded' in request.content_type:
        # empty url
        url = request.data.get('url')
        print(url)
        if not url:
            raise ValidationError('"url" is not found in request data')

        # try to load json with task or tasks from url as string
        json_data = str_to_json(url)
        if json_data:
            file_upload = create_file_upload(request, project, SimpleUploadedFile('inplace.json', url.encode()))
            file_upload_ids.append(file_upload.id)
            tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)
            
        # download file using url and read tasks from it
        else:
            data_keys, found_formats, tasks, file_upload_ids = tasks_from_url(
                file_upload_ids, project, request, url
            )

    # take one task from request DATA
    elif 'application/json' in request.content_type and isinstance(request.data, dict):
        tasks = [request.data]

    # take many tasks from request DATA
    elif 'application/json' in request.content_type and isinstance(request.data, list):
        tasks = request.data

    # incorrect data source
    else:
        raise ValidationError('load_tasks: No data found in DATA or in FILES')

    # check is data root is list
    if not isinstance(tasks, list):
        raise ValidationError('load_tasks: Data root must be list')

    # empty tasks error
    if not tasks:
        raise ValidationError('load_tasks: No tasks added')

    check_max_task_number(tasks)
    return tasks, file_upload_ids, could_be_tasks_lists, found_formats, list(data_keys)

