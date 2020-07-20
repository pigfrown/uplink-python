# pylint: disable=too-many-arguments
""" example project for storj-python binding shows how to use binding for various tasks. """
import os
import sys
from datetime import datetime

from uplink_python.constants import ERROR_BUCKET_NOT_EMPTY
from uplink_python.exchange import DownloadOptions
from uplink_python.uplink import LibUplinkPy, ListObjectsOptions, Permission, c


def upload_file(storj_obj, project, bucket_name, storj_path, upload_options, src_full_filename):
    """
    example function to put/upload data from src_full_filename (at local computer) to
    Storj (V3) bucket's path
    """
    #
    # open file to be uploaded
    DownloadOptions()
    file_handle = open(src_full_filename, 'r+b')
    data_len = os.path.getsize(src_full_filename)
    #
    # call to get uploader handle
    upload_result, error = storj_obj.upload_object(project, bucket_name, storj_path,
                                                   upload_options)
    if error is not None:
        return False, error
    #
    # initialize local variables and start uploading packets of data
    uploaded_total = 0
    while uploaded_total < data_len:
        # set packet size to be used while uploading
        size_to_write = 256 if (data_len - uploaded_total > 256) else data_len - uploaded_total
        #
        # exit while loop if nothing left to upload
        if size_to_write == 0:
            break
        #
        # file reading process from the last read position
        file_handle.seek(uploaded_total)
        data_to_write = file_handle.read(size_to_write)
        #
        # --------------------------------------------
        # data conversion to type required by function
        # get size of data in c type int32 variable
        # conversion of read bytes data to c type ubyte Array
        data_to_write = (c.c_uint8 * c.c_int32(len(data_to_write)).value)(*data_to_write)
        # conversion of c type ubyte Array to LP_c_ubyte required by upload write function
        data_to_write_ptr = c.cast(data_to_write, c.POINTER(c.c_uint8))
        # --------------------------------------------
        #
        # call to write data to Storj bucket
        write_result, error = storj_obj.upload_write(upload_result.upload, data_to_write_ptr,
                                                     size_to_write)
        if error is not None:
            return False, error
        #
        # exit while loop if nothing left to upload / unable to upload
        if int(write_result.bytes_written) == 0:
            break
        # update last read location
        uploaded_total += int(write_result.bytes_written)

    # commit upload data to bucket
    error = storj_obj.upload_commit(upload_result.upload)
    #
    # if error occurred
    if error is not None:
        return False, error
    return True, None


def download_file(storj_obj, project, bucket_name, storj_path, download_options,
                  dest_full_pathname):
    """
    example function to get/download Storj(V3) object's data and store it in given file
    with dest_full_pathname (on local computer)
    """
    #
    # open / create file with the given name to save the downloaded data
    file_handle = open(dest_full_pathname, 'w+b')
    #
    # call to get downloader handle
    download_result, error = storj_obj.download_object(project, bucket_name, storj_path,
                                                       download_options)
    if error is not None:
        return False, error
    #
    # get size of file to be downloaded from storj
    file_size, error = get_file_size(storj_obj, project, bucket_name, storj_path)
    if error is not None:
        return False, error
    print("File size to be downloaded: ", file_size)
    #
    # set packet size to be used while downloading
    size_to_read = 256
    # initialize local variables and start downloading packets of data
    downloaded_total = 0
    while True:
        # call to read data from Storj bucket
        data_read_ptr, read_result, error = storj_obj.download_read(download_result.download,
                                                                    size_to_read)
        if error is not None:
            return False, error
        #
        # file writing process from the last written position if new data is downloaded
        if int(read_result.bytes_read) != 0:
            #
            # --------------------------------------------
            # data conversion to type python readable form
            # conversion of LP_c_ubyte to python readable data variable
            data_read = c.string_at(data_read_ptr, int(read_result.bytes_read))
            # --------------------------------------------
            #
            file_handle.seek(downloaded_total)
            file_handle.write(data_read)
        #
        # update last read location
        downloaded_total += int(read_result.bytes_read)
        #
        # break if download complete
        if downloaded_total == file_size:
            break
    #
    # close downloader and free downloader access
    error = storj_obj.close_download(download_result.download)
    #
    # if error occurred
    if error is not None:
        return False, error
    return True, None


def get_file_size(storj_obj, project, bucket_name, storj_path):
    """
    example function to get Storj(V3) object's size to be downloaded
    """
    #
    # get object data
    obj_result, error = storj_obj.stat_object(project, bucket_name, storj_path)
    if error is not None:
        return 0, error
    # find object size
    return int(obj_result.object.contents.system.content_length), None


if __name__ == "__main__":

    # Storj configuration information
    MY_API_KEY = "change-me-to-the-api-key-created-in-satellite-gui"
    MY_SATELLITE = "us-central-1.tardigrade.io:7777"
    MY_BUCKET = "my-first-bucket"
    MY_STORJ_UPLOAD_PATH = "(optional): path / (required): filename"
    # (path + filename) OR filename
    MY_ENCRYPTION_PASSPHRASE = "you'll never guess this"

    # Source and destination path and file name for testing
    SRC_FULL_FILENAME = "filename with extension of source file on local system"
    DESTINATION_FULL_FILENAME = "filename with extension to save on local system"

    # create an object of libUplinkPy class
    StorjObj = LibUplinkPy()

    # function calls
    # request access using passphrase
    print("\nRequesting Access using passphrase...")
    access_result, err = StorjObj.request_access_with_passphrase(MY_SATELLITE, MY_API_KEY,
                                                                 MY_ENCRYPTION_PASSPHRASE)
    if err is not None:
        print(err)
        sys.exit()
    print("Request Access: SUCCESS!")
    #

    # open Storj project
    print(
        "\nOpening the Storj project, corresponding to the parsed Access, on " + MY_SATELLITE +
        " satellite...")
    project_result, err = StorjObj.open_project(access_result.access)
    if err is not None:
        print(err)
        sys.exit()
    print("Desired Storj project: OPENED!")
    #

    # enlist all the buckets in given Storj project
    print("\nListing bucket's names and creation time...")
    bucket_list, err = StorjObj.list_buckets(project_result.project, None)
    if err is not None:
        print(err)
        sys.exit()
    else:
        # print all bucket name and creation time
        for item in bucket_list:
            print(item.contents.name.decode("utf-8"), " | ",
                  datetime.fromtimestamp(item.contents.created))
        print("Buckets listing: COMPLETE!")
    #

    # delete given bucket
    print("\nDeleting '" + MY_BUCKET + "' bucket...")
    bucket_result, err = StorjObj.delete_bucket(project_result.project, MY_BUCKET)
    if err is not None:
        print(err)
    else:
        print("Desired bucket: DELETED")
    #

    # if delete bucket fails due to "not empty", delete all the objects and try again
    if bool(bucket_result.error):
        if ERROR_BUCKET_NOT_EMPTY == bucket_result.error.contents.code:
            print("\nDeleting object's inside bucket and try to delete bucket again...")
            # set list options before calling list objects (optional)
            listOption = ListObjectsOptions()
            listOption.recursive = True
            # list objects in given bucket with above options
            print("Listing and deleting object's inside bucket...")
            objects_list, err = StorjObj.list_objects(project_result.project, MY_BUCKET,
                                                      listOption)
            if err is not None:
                print(err)
            else:
                # iterate through all objects path
                for obj in objects_list:
                    # delete selected object
                    print("Deleting '" + obj.contents.key.decode('utf-8'))
                    object_result, err = StorjObj.delete_object(project_result.project, MY_BUCKET,
                                                                obj.contents.key.decode('utf-8'))
                print("Delete all objects inside the bucket : COMPLETE!")

                # try to delete given bucket
                print("\nDeleting '" + MY_BUCKET + "' bucket...")
                bucket_result, err = StorjObj.delete_bucket(project_result.project, MY_BUCKET)
                if err is not None:
                    print(err)
                else:
                    print("Desired bucket: DELETED")
    #

    # create bucket in given project
    print("\nCreating '" + MY_BUCKET + "' bucket...")
    bucket_result, err = StorjObj.ensure_bucket(project_result.project, MY_BUCKET)
    if err is not None:
        print(err)
        sys.exit()
    print("Desired Bucket: CREATED!")

    # as an example of 'put' , lets read and upload a local file
    # upload file/object
    print("\nUploading data...")
    uploadStatus, err = upload_file(StorjObj, project_result.project, MY_BUCKET,
                                    MY_STORJ_UPLOAD_PATH, None, SRC_FULL_FILENAME)
    if err is not None or uploadStatus is False:
        print(err)
        sys.exit()
    print("Upload: COMPLETE!")
    #
    #
    # set list options before calling list objects (optional)
    listOption = ListObjectsOptions()
    listOption.recursive = True
    # list objects in given bucket with above options or None
    print("\nListing object's names...")
    objects_list, err = StorjObj.list_objects(project_result.project, MY_BUCKET, listOption)
    if err is not None:
        print(err)
        sys.exit()
    else:
        # print all objects path
        for obj in objects_list:
            print(obj.contents.key.decode('utf-8'))
        print("Objects listing: COMPLETE!")
    #

    # as an example of 'get' , lets download an object and write it to a local file
    # download file/object
    print("\nDownloading data...")
    downloadStatus, err = download_file(StorjObj, project_result.project, MY_BUCKET,
                                        MY_STORJ_UPLOAD_PATH, None, DESTINATION_FULL_FILENAME)
    if err is not None or downloadStatus is False:
        print(err)
        sys.exit()
    print("Download: COMPLETE!")
    #

    # as an example of how to create shareable Access for easy storj access without
    # API key and Encryption PassPhrase
    # create new Access with permissions
    print("\nCreating new Access...")
    # set permissions for the new access to be created
    permissions = Permission()
    permissions.allow_list = True
    permissions.allow_delete = False
    # set shared prefix as list of dictionaries for the new access to be created
    shared_prefix = [{"bucket": MY_BUCKET, "prefix": ""}]
    # create new access
    new_access_result, err = StorjObj.access_share(access_result.access, permissions, shared_prefix)
    if err is not None:
        print(err)
        sys.exit()
    print("New Access: CREATED!")
    #

    # generate serialized access to share
    print("\nGenerating serialized Access...")
    serialized_access_result, err = StorjObj.access_serialize(new_access_result.access)
    if err is not None:
        print(err)
        sys.exit()
    print("Serialized shareable Access: ", serialized_access_result.string.decode("utf-8"))
    #

    #
    # close given project using handle
    print("\nClosing Storj project...")
    err = StorjObj.close_project(project_result.project)
    if err is not None:
        print(err)
        sys.exit()
    print("Project CLOSED!")
    #

    #
    # as an example of how to retrieve information from shareable Access for storj access
    # retrieving Access from serialized Access
    print("\nParsing serialized Access...")
    shared_access_result, err = StorjObj.parse_access(serialized_access_result.string)
    if err is not None:
        print(err)
        sys.exit()
    print("Parsing Access: COMPLETE")
    #

    # open Storj project
    print(
        "\nOpening the Storj project, corresponding to the shared Access...")
    shared_project_result, err = StorjObj.open_project(shared_access_result.access)
    if err is not None:
        print(err)
        sys.exit()
    print("Desired Storj project: OPENED!")
    #

    # enlist all the buckets in given Storj project
    print("\nListing bucket's names and creation time...")
    bucket_list, err = StorjObj.list_buckets(shared_project_result.project, None)
    if err is not None:
        print(err)
        sys.exit()
    else:
        # print all bucket name and creation time
        for item in bucket_list:
            print(item.contents.name.decode("utf-8"), " | ",
                  datetime.fromtimestamp(item.contents.created))
        print("Buckets listing: COMPLETE!")
    #

    # set list options before calling list objects (optional)
    listOption = ListObjectsOptions()
    listOption.recursive = True
    # list objects in given bucket with above options or None
    print("\nListing object's names...")
    objects_list, err = StorjObj.list_objects(shared_project_result.project, MY_BUCKET,
                                              listOption)
    if err is not None:
        print(err)
        sys.exit()
    else:
        # print all objects path
        for obj in objects_list:
            print(obj.contents.key.decode('utf-8'))
        print("Objects listing: COMPLETE!")
    #

    # try to delete given bucket
    print("\nTrying to delete '" + MY_STORJ_UPLOAD_PATH)
    shared_object_result, err = StorjObj.delete_object(shared_project_result.project, MY_BUCKET,
                                                       MY_STORJ_UPLOAD_PATH)
    if err is not None:
        print(err)
    else:
        print("Desired object: DELETED")
    #

    #
    # close given project with shared Access
    print("\nClosing Storj project...")
    err = StorjObj.close_project(shared_project_result.project)
    if err is not None:
        print(err)
        sys.exit()
    print("Project CLOSED!")
    #
