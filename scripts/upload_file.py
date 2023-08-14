import shutil
import os
import logging
import argparse
import json
import requests

LOG_FILE_DIR = "~/.log/"
LOG_FILE_NAME = "upload.log"


def main():
    full_path = os.path.expanduser(LOG_FILE_DIR)
    if not os.path.exists(full_path):
        os.mkdir(full_path)

    parser = argparse.ArgumentParser(description='Upload a to zipline service')
    parser.add_argument('--files', nargs='+', help='files to upload')
    parser.add_argument('--service', help='service to upload to', default='https://upload.montague.im')
    parser.add_argument('--token', help='token to use', default=os.getenv('UPLOAD_TOKEN', None))
    parser.add_argument('--debug', help='debug mode', action='store_true')
    parser.add_argument('--keep-names', help='keep original names', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(filename=os.path.join(full_path, LOG_FILE_NAME), level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.debug(f"Args passed in {args}")

    if not shutil.which("notify-send"):
        logging.error("notify-send not found")

    if not args.token:
        logging.error("'❌ No token provided")
        os.system("notify-send '❌ No token provided'")
        return

    args.files = [file for file in args.files if os.path.exists(file)]

    if args.files is None or len(args.files) == 0:
        logging.error("'❌ No files provided")
        os.system("notify-send '❌ No files provided'")
        return
    # send a request with all files in one request
    files = [('file', (file, open(file, 'rb'))) for file in args.files]
    response = requests.post(f'{args.service}/api/upload', files=files, headers={'authorization': f'{args.token}'})

    # if args.keep_names and args.keep_names is True:
    # else:

    if response.status_code != 200:
        logging.error(f"Failed to upload file: {response.text}")
        os.system(f"notify-send '❌ Failed to upload file: {response.text}'")
        return

    js = json.loads(response.text)
    files = js['files']

    output = ""
    if len(files) != len(args.files):
        output += f"❌ Failed to upload {len(args.files) - len(files)} files\n\n"

    for file in files:
        file_name = file.split('/')[-1]
        output += f"✅ Uploaded {file_name} to {file}\n"

    os.system(f"notify-send '{output}'")
    logging.info(output)

    urls = [file for file in files]
    urls = '\n'.join(urls)

    os.system(f"echo '{urls}' | xsel -ib")


if __name__ == "__main__":
    main()
