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
        self._total_scrape_attempts = 0

    def start_scraper(self):

        if self._total_scrape_attempts > 1:
            self._shutdown()

        self.logger.info("Scraping...")
        instrument_paths = ["bass", "drum", "sounds"]
        self._ensure_local_directory_exists()

        for instrument in instrument_paths:

            for i in range(1, 16):
                destination_path = self._get_file_destination(instrument, i)

                if self._check_if_file_exists(destination_path):
                    res = self._make_request(instrument, i)
                else:
                    self.logger.info("%s already exists!", destination_path[24:])
                    continue

                try:

                    if res.status_code == 200:
                        self._write_file(res.raw, destination_path)
                    elif res.status_code == 404:
                        self.logger.debug(
                            "URL doesn't exist - %s out of range",
                            destination_path[6:])
                except Exception as e:
                    self.logger.warn(
                        "Received unexpected exception. Stopping scrape.", e)
                    self._shutdown()
        self._cleanup()

    def _make_request(self, instrument, n):
        full_url = self._get_full_url(instrument, n)
        self.logger.debug("Fetching %s", full_url)
        return requests.get(full_url, stream=True)

    def _get_full_url(self, instrument, n):
        url_base = "http://madeonwmas.s3-eu-west-1.amazonaws.com/assets/audio/"
        file_format = "{}.1.{}.ogg"
        full_url = url_base + file_format.format(instrument, n)
        return full_url

    def _ensure_local_directory_exists(self):
        relative_path = "AdventureMachineSamples/"
        os.makedirs(relative_path, exist_ok=True)

    def _check_if_file_exists(self, destination_path):
        return not os.path.isfile(destination_path)

    def _write_file(self, raw_response, destination_path):
        self.logger.info("Writing %s to %s",
                         destination_path[24:], destination_path[:24])
        with open(destination_path, "wb") as f:
            raw_response.decode_content = True
            shutil.copyfileobj(raw_response, f)
            f.close()

    def _get_file_destination(self, instrument, n):
        return"AdventureMachineSamples/{}.1.{}.ogg".format(instrument, n)

    def _cleanup(self):
        failed_downloads = []
        expected_files = {}
        expected_files["bass"] = list(range(1, 11))
        expected_files["drum"] = list(range(1, 11))
        expected_files["sounds"] = list(range(1, 16))

        for instrument in expected_files:

            for sample in expected_files[instrument]:
                expected_destination = self._get_file_destination(
                    instrument, sample)

                if os.path.exists(expected_destination) is False:
                    failed_downloads.append(expected_destination)

        if not failed_downloads:
            self.logger.info("All files successfully retrieved")
        elif failed_downloads:
            self.logger.warn("Error in writing file/download - %s should exist",
                             failed_downloads)
            self.logger.warn("Attempted to redownload")
            self._total_scrape_attempts += 1
            self.start_scraper()

    def _shutdown(self):
        self.logger.warn("After two attempts, cannot scrape files. Exiting...")

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


def main(args):
    log_fmt = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format=log_fmt)
    logger = logging.getLogger()

    # sets all loggers from requests library to warning, useful for --debug
    for key in logging.Logger.manager.loggerDict:
        logging.getLogger(key).setLevel(logging.WARNING)

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
