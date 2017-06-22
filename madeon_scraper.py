import argparse
import logging
import os
import requests
import shutil
import sys


class MadeonScraper(object):
    def __init__(self):
        self.logger = logging.getLogger()

        # TODO(and0r): move these to discrete method
        self.relative_path = "files/"
        self.instrument_paths = ['drum', 'bass', 'sounds']

    def start_scraper(self):
        self.logger.info("Starting to scrape...")
        self._ensure_local_directory_exists()

        for instrument in self.instrument_paths:

            for i in range(1, 16):
                file_name = "files/{}.1.{}.ogg".format(instrument, i)
                res = requests.get(
                    self._get_full_url().format(instrument, i), stream=True)

                try:

                    if res.status_code == 200:
                        self.logger.info("Response code %s - Downloading: %s",
                                         res.status_code, file_name[6:])
                        with open(file_name, 'wb') as f:
                            res.raw.decode_content = True
                            shutil.copyfileobj(res.raw, f)
                    elif res.status_code == 404:
                        self.logger.info("Url doesn't exist")
                except Exception as e:
                    self.logger.warn(
                        "Received unexpected exception. Stopping scrape.", e)

    # TODO(and0r): refactor this to include instruments in path
    def _get_full_url(self):
        # def _get_full_url(self, instrument):
        url_base = "http://madeonwmas.s3-eu-west-1.amazonaws.com/assets/audio/"
        file_format = "{}.1.{}.ogg"
        # instruments = ['drum', 'bass', 'sounds']
        # return url_base + file_format.format(instruments)
        return url_base + file_format

    # TODO(and0r): build this for file creation
    # def _get_file_destination(self):

    def _ensure_local_directory_exists(self):
        os.makedirs(self.relative_path, exist_ok=True)


def main(args):
    log_fmt = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format=log_fmt)
    logger = logging.getLogger()

    # Turns off logging
    if args.no_log:
        logger.disabled = True

    ms = MadeonScraper()
    try:
        ms.start_scraper()
    except KeyboardInterrupt:
        # newline makes logger more obvious
        print("\n")
        logger.warn(
            "Received KeyboardInterrupt. Stopping scrape.")

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Set logger level")
    parser.add_argument("--debug", action="store_true",
                        help="Sets logging to debug")
    parser.add_argument("--no_log", action="store_true",
                        help="Turns off all logging")
    args = parser.parse_args()

    main(args)
