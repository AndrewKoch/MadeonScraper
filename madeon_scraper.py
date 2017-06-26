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
        self.total_scrape_attempts = 0
        self.config = {
            "instruments": {
                "bass": 11,
                "drum": 11,
                "sounds": 16
                },
            "url_format": "http://madeonwmas.s3-eu-west-1.amazonaws.com/assets/audio/{}.1.{}.ogg"
            }

    def start_scraper(self):
        self.logger.info("Scraping...")
        self._ensure_local_directory_exists()

        for instrument in self.config["instruments"]:
            file_range = self.config["instruments"][instrument]
            for sample in range(1, file_range):
                destination_path = self._get_file_destination(instrument, sample)

                if not os.path.isfile(destination_path):
                    res = self._make_request(instrument, sample)
                else:
                    self.logger.info("%s already exists", destination_path[24:])
                    continue

                try:
                    if res.raise_for_status() is None:
                        self._write_file(res.raw, destination_path)
                    else:
                        self.logger.debug("URL doesn't exist - %s out of range",
                                          destination_path[6:])
                except Exception as e:
                    self.logger.error("Received unexpected exception", repr(e))
        self._cleanup()

    def _make_request(self, instrument, n):
        full_url = self._get_full_url(instrument, n)
        self.logger.debug("Fetching %s", full_url)
        return requests.get(full_url, stream=True)

    def _get_full_url(self, instrument, n):
        url = self.config["url_format"]
        return url.format(instrument, n)

    def _ensure_local_directory_exists(self):
        relative_path = "AdventureMachineSamples/"
        os.makedirs(relative_path, exist_ok=True)

    def _write_file(self, raw_response, destination_path):
        self.logger.info("Writing %s to %s",
                         destination_path[24:], destination_path[:24])
        with open(destination_path, "wb") as f:
            raw_response.decode_content = True
            shutil.copyfileobj(raw_response, f)

    def _get_file_destination(self, instrument, n):
        return "AdventureMachineSamples/{}.1.{}.ogg".format(instrument, n)

    def _cleanup(self):
        failed_downloads = []

        for instrument in self.config["instruments"]:
            file_range = self.config["instruments"][instrument]
            for sample in range(1, file_range):
                expected_destination = self._get_file_destination(
                    instrument, sample)

                if not os.path.exists(expected_destination):
                    failed_downloads.append(expected_destination)

        if not failed_downloads:
            self.logger.info("All files successfully retrieved")
        elif self.total_scrape_attempts < 2:
            self.logger.warn("Attempting to redownload...")
            self.total_scrape_attempts += 1
            self.start_scraper()
        else:
            self.logger.error("Failed to fetch {}".format(failed_downloads))


def main(args):
    log_fmt = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # sets requests and urllib3 loggers to warning, useful for --debug
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
    logger.error("%s raised - Exiting...", e.__class__.__name__)

    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Scrapes audio from Madeon's Adventure Machine")
    parser.add_argument("--debug", action="store_true",
                        help="Sets logging to debug")
    parser.add_argument("--no-log", action="store_true",
                        help="Turns off all logging")
    args = parser.parse_args()

    main(args)
