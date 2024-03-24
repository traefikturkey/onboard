# cafe_hayek.py
import re
class CafeHayek:
    def process(self, data):
        for article in data['articles']:
            article['summary'] = re.sub(r'^Tweet\s*\.{0,3}|\…\s+', '', article['summary'])
            print(article['summary'])
        return data
