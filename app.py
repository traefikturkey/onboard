from flask import Flask, render_template
import feedparser

app = Flask(__name__)

# Define the list of RSS feed URLs
RSS_FEEDS = {
    'BBC': 'http://feeds.bbci.co.uk/news/rss.xml',
    'CNN': 'http://rss.cnn.com/rss/edition.rss',
    'NY Times': 'http://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'
}

# Function to parse RSS feeds
def get_news(feed_url):
    feed = feedparser.parse(feed_url)
    return feed['entries']

# Route for home page
@app.route('/')
def index():
    # Get news from each feed
    news = {source: get_news(url) for source, url in RSS_FEEDS.items()}
    return render_template('index.html', news=news)

if __name__ == '__main__':
    app.run(debug=True)
