import re


class Instapundit:
  def process(self, data):
    for article in data['articles']:
      article['title'] = re.sub(r'http[s]?://\S+', '', article['title'], flags=re.IGNORECASE)

    return data
