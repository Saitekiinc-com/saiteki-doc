# c-rails-01: 内部Railsアプリサーバー
# 古いRailsバージョン、既知の脆弱性を含む設定

FROM ruby:3.1-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    net-tools \
    iputils-ping \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Gemfile (古いgemを含む)
COPY Gemfile Gemfile.lock* ./
RUN bundle install

COPY . .

# DBマイグレーション & サーバー起動
EXPOSE 3000

CMD ["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]
