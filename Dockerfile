# syntax=docker/dockerfile:1.3-labs 
FROM ruby:3-alpine AS base

ARG APP_USER=anvil
ARG GEM_HOME=/usr/local/bundle

ENV APP=/app
ENV HOME=$APP
ENV GEM_HOME=${GEM_HOME}
ENV PATH=$APP/bin:$GEM_HOME/bin:$PATH

ENV LANGUAGE=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV TZ=America/New_York

RUN apk --no-cache add \
  bash \
  ca-certificates \
  curl \
  tzdata && \
  ln -snf /etc/localtime /usr/share/zoneinfo/$TZ && echo $TZ > /etc/timezone && \
  addgroup -S $APP_USER && \
  adduser -SDH -s /sbin/nologin -G $APP_USER $APP_USER && \
  mkdir -p $APP && \
  chown $APP_USER:$APP_USER $APP && \
  echo "alias l='ls -lhav --color=auto --group-directories-first'" >> /etc/profile.d/aliases.sh && \
  echo "PS1='\h:\$(pwd) \$ '" >> /etc/profile.d/prompt.sh && \
  rm -rf /var/cache/apk/* 

WORKDIR $APP

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb", "config.ru"]

##############################
# Begin DEV 
##############################
FROM base AS dev

RUN apk --no-cache add \
  build-base && \
  rm -rf /var/cache/apk/* 

COPY ./base/Gemfile* $APP
RUN bundle install 




##############################
# Begin PROD 
##############################
FROM base AS prod

# copy gems from dev
COPY --from=dev ${GEM_HOME} ${GEM_HOME}
COPY --chown=$APP_USER:$APP_USER ./base/ /app

USER $APP_USER