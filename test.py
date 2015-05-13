#!/usr/bin/env python
"""
Very basic logcrypt unit tests
"""

import os
import unittest
import logcrypt

class LogCryptTests(unittest.TestCase):

    def setUp(self):
        self.recipient = "smwood4@gmail.com"
        self.s3_bucket = "fake_bucket"
        self.s3_prefix = "fake_prefix"

        # Set the environment variables
        os.environ["AWS_ACCESS_KEY_ID"] = "fake_id"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "fake_key"
        os.environ["KEY_SERVER"] = "pgp.mit.edu"
        os.environ["KEY_HASH"] = "40F62752"

    def test_import_logcrypt(self):
        "Test whether or not import fails"
        logcrypt.LogCrypt(self.recipient, self.s3_bucket, self.s3_prefix)

    def test_no_aws_key_fail(self):
        "Test for failure if AWS key and ID are not present"
        del os.environ["AWS_ACCESS_KEY_ID"]
        del os.environ["AWS_SECRET_ACCESS_KEY"]
        with self.assertRaises(Exception):
            logcrypt.LogCrypt(self.recipient, self.s3_bucket, self.s3_prefix)

if __name__ == '__main__':
    unittest.main()
