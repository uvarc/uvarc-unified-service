FROM python:3.12.6
LABEL maintainer="rkc7h@virginia.edu"

ENV NON_ROOT_USER=non_root_user
ENV NON_ROOT_GID="103" \
    NON_ROOT_UID="1003" \
    NON_ROOT_WORK_DIR=/opt/local/${NON_ROOT_USER} \
    NON_ROOT_HOME_DIR=/home/${NON_ROOT_USER}
RUN groupadd -g 65532 nonroot && useradd -m -s $NON_ROOT_HOME_DIR -u 65532 $NON_ROOT_USER -g nonroot
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends nginx supervisor\
    && echo "user $NON_ROOT_USER;" >> /etc/nginx/nginx.conf \
    && echo "daemon off;" >> /etc/nginx/nginx.conf \
    && apt-get install -y sudo \
    # && echo $NON_ROOT_USER ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$NON_ROOT_USER \
    # && chmod 0440 /etc/sudoers.d/$NON_ROOT_USER \
    && apt-get clean \
    && apt-get auto-remove -y \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*
RUN chmod g+wx /var/log/
ENV APP_LOC $NON_ROOT_WORK_DIR/uvarc_unified_service
WORKDIR $APP_LOC
RUN sudo mkdir -p $NON_ROOT_WORK_DIR && \
    sudo mkdir -p $APP_LOC
RUN sudo mkdir  -p  /var/lib/nginx/body
RUN sudo mkdir  -p  /var/lib/nginx/fastcgi
RUN sudo mkdir  -p  /var/lib/nginx/proxy
RUN sudo mkdir  -p  /var/lib/nginx/uwsgi
RUN sudo mkdir  -p  /var/lib/nginx/scgi
RUN sudo chown  -R www-data  /var/lib/nginx
RUN sudo chown  -R $NON_ROOT_USER /var/lib/nginx

ADD ./requirements.txt .
RUN pip3 install -r requirements.txt
RUN supervisord -v
RUN pip3 install supervisor
RUN supervisord -v
ENV FLASK_APP app/__init__.py
ENV FLASK_DEBUG 0
ADD ./nginx_app.conf /etc/nginx/sites-available/default
ADD ./supervisor_app.conf /etc/supervisor/conf.d/supervisor_app.conf
ADD ./supervisor_app.conf /etc/supervisor/supervisord.conf
ADD ./. .
RUN cd instance && ln -sf ../config/base.py settings.py && cd ../
RUN chgrp -R nonroot $APP_LOC && chown -R $NON_ROOT_USER $APP_LOC
RUN chgrp -R nonroot /etc/nginx && chown -R $NON_ROOT_USER /etc/nginx
RUN chgrp -R nonroot /var/log/ && chown -R $NON_ROOT_USER /var/log/
RUN cp nginx.conf /etc/nginx/nginx.conf && chmod -R g+wx /etc/nginx/
RUN rm -rf /usr/bin/python2
EXPOSE 5000
USER $NON_ROOT_USER
CMD ["supervisord"]
