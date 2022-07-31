# frozen_string_literal: true
require 'rss'
require 'open-uri'
require 'htmlentities'

class RssFeedComponent < ViewComponent::Base
  attr_reader :url, :html

  def initialize(url:)
    @url = url
    @html = HTMLEntities.new
  end

  def feed
    Rails.cache.fetch( self.url, expires_in: 5.minutes) do
      URI.open(url) do |rss|
        feed = RSS::Parser.parse(rss)
      end
    end
  end

  def decode(string)
    html.decode(string)
  end

end