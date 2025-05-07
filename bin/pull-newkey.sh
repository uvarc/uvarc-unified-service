#!/bin/bash

RCMD+="/bin/bash "
RCMD+="$REMOTE_SCRIPT"

/usr/bin/ssh -oStrictHostKeyChecking=no -i /etc/ssh-key/id_rsa $USERID@login.hpc.virginia.edu $RCMD
