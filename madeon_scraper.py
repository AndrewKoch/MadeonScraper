#!/usr/bin/env python3

"""Scrapes audio files from Madeon's awesome Adventure Machine"""

import argparse
import logging
import os
import requests
import shutil
import sys
import threading


class MadeonScraper(object):
    def __init__(self):
        self.logger = logging.getLogger()
        self._total_scrape_attempts = 0

    def start_scraper(self):
        self.logger.info("Scraping...")
        instrument_paths = ["bass", "drum", "sounds"]
        self._ensure_local_directory_exists()

        for instrument in instrument_paths:

            for i in range(1, 16):
                destination_path = self._get_file_destination(instrument, i)

                if self._check_if_file_exists(destination_path):
                    res = self._make_request(instrument, i)
                else:
                    self.logger.info("%s already exists", destination_path[24:])
                    continue

                try:

                    if res.status_code == 200:
                        self._write_file(res.raw, destination_path)
                    elif res.status_code == 404:
                        self.logger.debug("URL doesn't exist - %s out of range",
                                          destination_path[6:])
                except Exception as e:
                    raise Exception("Received unexpected exception", e)
        self._cleanup()

    def _make_request(self, instrument, n):
        full_url = self._get_full_url(instrument, n)
        self.logger.debug("Fetching %s", full_url)
        return requests.get(full_url, stream=True)

    def _get_full_url(self, instrument, n):
        url_base = "http://madeonwmas.s3-eu-west-1.amazonaws.com/assets/audio/"
        file_format = "{}.1.{}.ogg"
        return url_base + file_format.format(instrument, n)

    def _ensure_local_directory_exists(self):
        """Makes directory if it doesn't exist. Throws no exception"""
        relative_path = "AdventureMachineSamples/"
        os.makedirs(relative_path, exist_ok=True)

    def _check_if_file_exists(self, destination_path):
        """os.path.isfile(path) returns True if file exists"""
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

            if self._total_scrape_attempts < 2:
                self.logger.warn("Attempting to redownload...")
                self._total_scrape_attempts += 1
                self.start_scraper()

            self.logger.warn("Could not complete download after two attempts")
            raise IOError


def main(args):
    log_fmt = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # sets all loggers from requests library to warning, useful for --debug
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.basicConfig(level=level, format=log_fmt)
    logger = logging.getLogger()

    # Turns off logging
    if args.no_log:
        logger.disabled = True

    try:
        ms = MadeonScraper()
        thread = threading.Thread(target=ms.start_scraper())
        thread.start()
    except (KeyboardInterrupt, IOError, Exception) as e:
        exception_handler(e, logger)


def exception_handler(e, logger):
    # newline makes logger more obvious
    print("\n")
    logger.warn("Exiting...")

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
