"""Download all files under the target google drive folder
"""
import io
import logging
import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools
from pathlib import Path

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.apps.readonly',
]

DOWNLOAD_PATH = '{PATH_TO_SAVE_FILE}' # change this variable

logger = logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('downloader.log')
fh.setLevel(logging.ERROR)

class DownloadFailException(Exception):
    pass

def download_media(service, path, file):
    file_name = path + file['name']
    f = Path(file_name)
    if f.is_file():
        return

    request = service.files().get_media(fileId=file['id'])
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
        except Exception as e:
            logger.info(f"Fail while downloading {file['name']}")
            logger.info(e)
            print('Download fail :(')
            raise DownloadFailException(e)
        print ("Download %d%%." % int(status.progress() * 100))

    return

def dfs(service, path, folder_id):
    nextPageToken = ''
    folder_list = list()
    file_list = list()
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            pageToken=nextPageToken,
            spaces='drive',
            pageSize=50,
            fields="nextPageToken, files(id, name, mimeType)").execute()
        nextPageToken = results.get('nextPageToken', )
        items = results.get('files', [])

        if not items:   
            print('No files found.')
        else:
            for item in items:
                if 'folder' in item['mimeType']:
                    folder_list.append(item)
                elif 'video' in item['mimeType']:
                    file_list.append(item)
                print(u'{0} ({1}) ({2})'.format(item['name'], item['id'], item['mimeType']))

        if not nextPageToken:
            break

    for file in file_list:
        print(f"Download file [{file['name']}]")
        try:
            download_media(service, path,  file)
        except DownloadFailException:
            # retry download
            print('Retrying...')
            download_media(service, path,  file)

    for folder in folder_list:
        new_path = DOWNLOAD_PATH + folder['name'] + '/'
        try:
            os.makedirs(new_path)
        except Exception as e:
            pass
        dfs(service, new_path, folder['id'])


def main():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('token.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))

    target_folder_id = '{GOOGLE_DRIVE_FOLDER_ID}' # change this variable
    dfs(service, DOWNLOAD_PATH, target_folder_id)

if __name__ == '__main__':
    main()