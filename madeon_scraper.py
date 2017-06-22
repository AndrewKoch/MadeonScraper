#!/usr/bin/env python3

import argparse
import logging
import os
import requests
import shutil
import sys


class MadeonScraper(object):
    def __init__(self):
        self.logger = logging.getLogger()

    def start_scraper(self):
        self.logger.info("Starting to scrape...")
        instrument_paths = ["bass", "drum", "sounds"]

        self._ensure_local_directory_exists()

        for instrument in instrument_paths:

            for i in range(1, 16):
                destination_path = self._get_file_destination(instrument, i)
                res = self._make_request(instrument, i)

                try:

                    if res.status_code == 200:
                        self._write_file(res.raw, destination_path)
                    elif res.status_code == 404:
                        self.logger.info(
                            "URL doesn't exist - %s out of range",
                            destination_path[6:])
                except Exception as e:
                    self.logger.warn(
                        "Received unexpected exception. Stopping scrape.", e)

    def _make_request(self, instrument, n):
        response = requests.get(self._get_full_url(instrument, n), stream=True)
        return response

    def _get_full_url(self, instrument, n):
        url_base = "http://madeonwmas.s3-eu-west-1.amazonaws.com/assets/audio/"
        file_format = "{}.1.{}.ogg"
        full_url = url_base + file_format.format(instrument, n)
        return full_url

    def _get_file_destination(self, instrument, n):
        return"files/{}.1.{}.ogg".format(instrument, n)

    def _write_file(self, raw_response, destination_path):

        if os.path.isfile(destination_path):
            self.logger.info("%s already exists!", destination_path[6:])
        else:
            self.logger.info("Writing %s to file", destination_path[6:])
            with open(destination_path, "wb") as f:
                raw_response.decode_content = True
                shutil.copyfileobj(raw_response, f)
                f.close()

    def _ensure_local_directory_exists(self):
        relative_path = "files/"
        os.makedirs(relative_path, exist_ok=True)


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
