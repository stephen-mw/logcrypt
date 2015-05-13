FROM phusion/baseimage

ENV USER=logcrypt
ENV HOME=/home/$USER

RUN apt-get update -y
RUN apt-get install -y --no-install-recommends gcc python-pip python-dev \
    python-virtualenv gnupg

# Install the requirements as the logcrypt user
RUN useradd -s /bin/false -m $USER
RUN /sbin/setuser $USER mkdir -p /home/$USER/.virtenv/
RUN /sbin/setuser $USER virtualenv /home/$USER/.virtenv/
RUN chown -R $USER:$USER /home/$USER

# Install python dependencies
ADD requirements.txt /tmp/requirements.txt
RUN chown $USER /tmp/requirements.txt
RUN /sbin/setuser $USER /home/$USER/.virtenv/bin/pip install -r /tmp/requirements.txt

ADD logcrypt.py /usr/local/bin/logcrypt.py
RUN chmod 755 /usr/local/bin/logcrypt.py

# Create the runit service
RUN mkdir -p /etc/service/logcrypt
ADD service_runit /etc/service/logcrypt/run

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 22 8080

# Start the watchdog process
CMD ["/sbin/my_init"]
