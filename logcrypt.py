#!/usr/bin/env python
"""
Encrypt and backup logs!

The logcrypt service will accept logs as a POST, encrypted/compress them with
a public GPG key, and then upload them to S3. For added security, data is never
persisted to disk. Logcrypt uses asymmetrical encryption, so not even the service
itself can decrypt the logs it's creating.

Using strong crypto helps keep your data secure, even in the event that your
S3 account gets compromised. The logs will also have the added benefit of being
compressed!

GPG uses standard POSIX users for gpg key management. The public key you want
to encrypt logs with must exist on the user's account that runs logcrypt. See
the official gpg documentation for importing a public key.
"""

import gnupg
import logging
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket
from StringIO import StringIO
from flask import Flask, request, jsonify

class LogCrypt(object):
    """
    Encrypt and upload logs to S3. This library assumes you've already imported
    your public key to the user's keychain that's using logcrypt. You can read
    more about the gpg keychain here:

        https://www.gnupg.org/gph/en/manual.html

    Args:
        recipient:  (str) the recipient to use for gpg encrypting. Must exist on
                    the logcrypt user's gpg keychain. Example: smwood4@gmail.com
        s3_bucket:  (str) the s3 bucket to use when uploading logs. Omit the
                    "s3://" prefix. Example: my_logs
        s3_prefix:  (str) Prefix to prepend to all files. Example "logs"
        port:       (int) The port to run the service.

    Required environment variables:

        AWS_ACCESS_KEY_ID
        AWS_SECRET_ACCESS_KEY

    """

    def __init__(self, recipient, s3_bucket, s3_prefix=None, port=8080):
        self.recipient = recipient
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.port = port

        self.logger = logging.getLogger(__name__)

        # Make sure you have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in
        # your environment or this will raise an exception.
        self.s3conn = S3Connection()

        self.gpg = self._init_gpg()
        self.logger.info("Valid recipients: %s", self.gpg.list_keys())

        if s3_prefix:
            self.logger.info("Logcrypt will upload files to bucket: %s",
                             self.s3_bucket + '/' + self.s3_prefix)
        else:
            self.logger.info("Logcrypt will upload files to bucket: %s", self.s3_bucket)

    def _init_gpg(self):
        "Helper function to Initialize the gpg object for encrypting files"

        keyring = os.environ['HOME'] + "/.gnupg/pubring.gpg"
        if not os.path.isfile(keyring):
            raise Exception("Keyring could not be found at %s. Make sure to "
                            "first import the public key" % keyring)
        gpg = gnupg.GPG(keyring=keyring)
        gpg.encoding = "latin-1"
        gpg.compress_algo = "ZLIB"

        return gpg

    def run_server(self):
        "Run the logcrypt webserver."

        app = Flask(__name__, static_url_path='')

        @app.route("/upload", methods=["POST"])
        def upload():
            '''
            Upload accepts binary data, encrypts it using the backups gpg key
            using asymmetrical encryption, and writes the file to the disk.
            '''
            minion = request.args.get('minion')
            self.logger.info(request.args)
            data = request.stream.read()
            if not data:
                return jsonify({"error": "No post data found!"}), 400

            # Check for required param and make sure it's not named something funny
            if not minion:
                return jsonify({"error": "Missing param: minion"}), 400

            # Create a string buffer in memory to write the data to
            minion_log = StringIO()
            minion_log.write(data)

            # Encrypt the file and write the output
            if self.s3_prefix:
                encrypted_file = self.s3_prefix + '/' + minion + '.gpg'
            else:
                encrypted_file = minion + '.gpg'

            self.logger.info("Creating: %s", encrypted_file)
            status = self.gpg.encrypt(minion_log.getvalue(), armor=False,
                                      recipients=[self.recipient])
            self.logger.info(status.status)
            minion_log.close()

            # Finally, upload the file. If we're unsuccesful at upload / encrypting
            # the file, then log the output and send a 500-error to the user
            try:
                bucket = Bucket(self.s3conn, self.s3_bucket)
                key = Key(bucket)
                key.key = encrypted_file
                key.set_contents_from_string(status.data)
            except Exception, err:
                self.logger.critical(err)
                return jsonify({"message": "Sorry. We couldn't encrypt that file. "
                                "Please try again later."}), 500

            if status.ok:
                return jsonify({"message": "File created"}), 201
            else:
                return jsonify({"message": "Sorry. We couldn't encrypt that file. "
                                "Please check the logs."}), 500

        # Run the webserver. This is blocking!
        try:
            app.run(threaded=True, host='0.0.0.0', port=self.port)
        except KeyboardInterrupt:
            exit(1)
        except Exception, err:
            self.logger.critical(err)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(name)s '
                        '%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
    logging.basicConfig()
    LOGGER = logging.getLogger()

    # Load the environment variables. This will raise a key error if there's
    # missing variable and the service will not run
    RECIPIENT = os.environ['GPG_RECIPIENT']
    S3_BUCKET = os.environ['UPLOAD_BUCKET']
    S3_PREFIX = os.environ['UPLOAD_PREFIX']

    LOGCRYPT = LogCrypt(RECIPIENT, S3_BUCKET, S3_PREFIX)

    try:
        LOGCRYPT.run_server()
    except Exception, err:
        LOGGER.critical(error)
