# Logcrypt - encrypt and backup logs!
[![Build Status](https://travis-ci.org/stephen-mw/logcrypt.svg)](https://travis-ci.org/stephen-mw/logcrypt)

Logcrypt is a service that allows for easy, encrypted backups of logs in cloud environments. Have all of your hosts simply make a POST to the logcrypt endpoint and logs will automatically be encrypted, compressed, and stored away in S3.

## Why
I manage a lot of hosts. Sometimes I spin up hundreds of them at one time. In order to save on costs, host bootstrapping has a built-in "self-destruct" method: if it senses something has gone wrong in its configuration, the host will automatically turn itself off to save money.

The mechnanism works great, but sometimes the host is shutoff even before monitoring or log shipping is turned on! To make it so post-mortems can always be completed, the instances will use logcrypt to securely upload their logs for a post-mortem regardless of where they are at in their bootstrap. The only thing they need is ```curl``` or some other way to make an HTTP POST.

## How it works
Logcrypt uses asymmetrical gpg encryption. A public gpg key is imported and aes 256-bit encryption is used. lza compression keeps the file size low and removes the need to compress logs before storage.

No files are ever persisted to disk. This helps bolster the security of logcrypt. And since logcrypt uses asymmetrical encryption, not even the service itself can decrypt files!

## Setup
Included is a Dockerfile for building the logcrypt container. Everything is controlled via environment variables.

Required environment variables:
* ```AWS_ACCESS_KEY_ID```: the aws id used to upload logs to S3
* ```AWS_SECRET_ACCESS_KEY```: the aws key used to upload logs to S3
* ```UPLOAD_BUCKET```: S3 bucket to upload logs
* ```UPLOAD_PREFIX```: This is the "folder" to store the file in in s3.
* ```GPG_RECIPIENT```: the gpg recipient as it is found in the gpg keychain. Typically this is something like ```contact.stephen.wood@gmail.com```
* ```KEY_SERVER```: keyserver to load the gpg public key from. E.g. ```pgp.mit.edu```
* ```KEY_HASH```: the key hash to load. E.g. ```40F62752```

When the logcrypt service starts for the first time, it will request a gpg public key from the keyserver specified in the environment variable.

The container itself uses the ubuntu 14.04 image from [phusion](https://github.com/phusion/baseimage-docker). Runit is used as the service manager.

## Using logcrypt
Once the logcrypt container is installed and running, you simply need to make a POST from any of your hosts.

```
$ curl -XPOST 10.30.40.240:8080/upload?minion=my-host --data-binary @/var/log/syslog
{
  "message": "File created"
}
```

minion is the name of the host. The log uploaded will be called "my-host.gpg"

Make sure that all of the environment variables are available to your container!
